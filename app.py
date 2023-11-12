from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import random

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


digits = list(range(0, 11))  # 0 to 10
colors = ['gold', 'silver', 'bronze', 'black']
special_cards = ['x', '√']
card_database = [] #generated

# Adding digit cards
for digit in digits:
    for color in colors:
        card_database.append(f"{digit}-{color}")

# Adding special cards
for card in special_cards:
    for _ in range(4):  # 4 copies of each special card
        card_database.append(card)
random.shuffle(card_database)

number_of_viewers = 0
current_round = 0
viewer_cards = {}
viewer_card_count = {}  # To keep track of how many cards each viewer has

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_viewers/<int:count>')
def set_viewers(count):
    global number_of_viewers
    number_of_viewers = count
    return jsonify({'message': 'Number of viewers set successfully'})

@app.route('/viewer/<viewer_id>')
def viewer(viewer_id):
    if viewer_id not in viewer_cards:
        viewer_cards[viewer_id] = ['+', '-', '÷']  # Initial cards
    return render_template('viewer.html', viewer_id=viewer_id)

@app.route('/get_card/<viewer_id>')
def get_card(viewer_id):
    global current_round, viewer_card_count
    if str(current_round) != viewer_id:
        return jsonify({'error': 'Not your turn'}), 403

    # Allow 2 cards per round if viewer already has 4 cards, otherwise 1 card
    max_cards_this_round = 2 if len(viewer_cards.get(viewer_id, [])) == 4 else 1

    if viewer_card_count.get(viewer_id, 0) >= max_cards_this_round:
        return jsonify({'error': f'You can only get {max_cards_this_round} cards for this round'}), 403

    if viewer_id in viewer_cards and card_database:
        cards_drawn_this_round = 0
        while cards_drawn_this_round < max_cards_this_round:
            new_card = card_database.pop(0)  # Draw a card
            if new_card not in ['x', '√'] or len(viewer_cards[viewer_id]) == 3:
                viewer_cards[viewer_id].append(new_card)
                cards_drawn_this_round += 1

        viewer_card_count[viewer_id] = cards_drawn_this_round  # Update the count for this round
    return jsonify(viewer_cards.get(viewer_id, []))




@app.route('/next_round')
def next_round():
    global current_round, viewer_card_count
    if number_of_viewers <= 0:
        return jsonify({'error': 'Number of viewers not set'}), 400
    # if str(current_round) not in viewer_card_count or viewer_card_count[str(current_round)] < 4:
    #     return jsonify({'error': 'You cannot pass the round yet'}), 403
    current_round = (current_round + 1) % number_of_viewers
    viewer_card_count = {k: (v if v < 4 else 3) for k, v in viewer_card_count.items()}
    return jsonify({'new_round': current_round})

@app.route('/get_all_cards')
def get_all_cards():
    return jsonify(viewer_cards)

@app.route('/get_round')
def get_round():
    return jsonify({'current_round': current_round})

if __name__ == '__main__':
    socketio.run(app, debug=True)