import streamlit as st
import pandas as pd
import os
import pickle
import chess.pgn
import chess
from evals_calc import evaluate_performance

# Load the trained model
def load_model(model_path='best_chess_model.pkl'):
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model

# Function to parse PGN and extract relevant features
def parse_pgn(pgn_file):
    with open(pgn_file) as f:
        game = chess.pgn.read_game(f)

    # Extract metadata
    white_elo = int(game.headers['WhiteElo'])
    black_elo = int(game.headers['BlackElo'])
    time_control = game.headers['TimeControl']
    white_ratting_diff = float(game.headers['WhiteRatingDiff'])
    black_ratting_diff = float(game.headers['BlackRatingDiff'])
    white_performance, black_performance = evaluate_performance(game)
    
    # Determine the result of the game
    result = game.headers['Result']
    if result == '1-0':  # White wins
        white_wins = 1
        black_wins = 0
        draw = 0
    elif result == '0-1':  # Black wins
        white_wins = 0
        black_wins = 1
        draw = 0
    else:  # Draw
        white_wins = 0
        black_wins = 0
        draw = 1

    # Extract moves
    moves = []
    for move in game.mainline_moves():
        moves.append(move.uci())

    # Flatten the moves
    flattened_encoded_moves = [item for move in moves for item in list(move)]
    
    # Calculate some basic features
    num_moves = len(moves)
    max_move_length = max(len(move) for move in moves)

    # Extract new features: ECO and Opening
    eco = game.headers.get('ECO', 'Unknown')  
    opening = game.headers.get('Opening', 'Unknown')  

    # Feature vector with the updated features
    feature_vector = [num_moves, max_move_length, time_control, white_performance, black_performance,
                      white_elo, black_elo, white_wins, black_wins, draw, white_ratting_diff, black_ratting_diff, eco, opening]

    return feature_vector, flattened_encoded_moves, moves

# Use the saved model to make predictions
def predict_white_elo(model, feature_vector):
    # Define the column names as used during model training
    column_names = ['Num_Moves', 'Max_Move_Length', 'TimeControl', 'White_Performance', 'Black_Performance', 
                    'WhiteElo', 'BlackElo', 'White_Wins', 'Black_Wins', 'Draw', 'WhiteRatingDiff', 
                    'BlackRatingDiff', 'ECO', 'Opening']
    df = pd.DataFrame([feature_vector], columns=column_names)
    
    # Use the model (preprocessor is already fitted inside the pipeline)
    predicted_white_elo = model.predict(df)
    return predicted_white_elo[0]

# Convert chess board to HTML representation
def render_chessboard(board):
    
    # Unicode symbols for chess pieces
    piece_symbols = {
        'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟',
        'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙'
    }
    
    # Generate HTML for the chessboard
    html = '<div style="display: grid; grid-template-columns: repeat(8, 60px); grid-template-rows: repeat(8, 60px); gap: 0px;">'
    
    for row in range(8):
        for col in range(8):
            # Use light brown for white squares and dark brown for black squares
            square_color = '#D2B48C' if (row + col) % 2 == 0 else '#8B4513'  # Light brown and dark brown squares
            
            piece = board.piece_at(8 * row + col)
            piece_html = ''
            if piece:
                piece_symbol = piece.symbol()
                piece_html = f'<span style="font-size: 40px; color: white;">{piece_symbols.get(piece_symbol, "")}</span>'
            
            # Create the square with the specified color and piece symbol
            html += f'<div style="background-color: {square_color}; display: flex; justify-content: center; align-items: center; height: 60px; width: 60px;">{piece_html}</div>'
    
    html += '</div>'
    
    return html

# Streamlit app
def main():
    st.title("Chess Elo Prediction App")

    # Set custom styling
    st.markdown("""
    <style>
    body {
        background-color: #f4f4f9;
        color: #333;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
    }
    .stFileUploader>label {
        background-color: #2196F3;
        color: white;
    }
    h1 {
        color: #3f51b5;
    }
    </style>
    """, unsafe_allow_html=True)

    # Upload PGN file
    pgn_file = st.file_uploader("Upload PGN file", type=['pgn'])

    if pgn_file is not None:
        # Save the uploaded PGN file temporarily
        with open("temp_game.pgn", "wb") as f:
            f.write(pgn_file.getbuffer())

        # Load the trained model (which includes the preprocessor)
        model = load_model('best_chess_model.pkl')

        # Parse the PGN file and extract features
        feature_vector, flattened_encoded_moves, moves = parse_pgn("temp_game.pgn")

        # Make a prediction for White Elo
        predicted_white_elo = predict_white_elo(model, feature_vector)

        # Display the result
        st.markdown(f"### Predicted White Elo: {int(predicted_white_elo)}", unsafe_allow_html=True)
        
        #display gamme details
        st.subheader("Game Details:")
        st.write(f"Number of Moves: {feature_vector[0]}")
        st.write(f"White Elo: {feature_vector[5]}")
        st.write(f"Black Elo: {feature_vector[6]}")
        st.write(f"White Wins: {feature_vector[7]}")
        st.write(f"Black Wins: {feature_vector[8]}")
        st.write(f"Draw: {feature_vector[9]}")
        
        # Initialize the board
        board = chess.Board()

        # Create session state variables to store game progress
        if "current_move" not in st.session_state:
            st.session_state.current_move = 0
            st.session_state.board = board
        else:
            board = st.session_state.board

        # Display the interactive chessboard using custom HTML and CSS
        st.subheader("Chess Game Visualization")
        st.markdown(render_chessboard(board), unsafe_allow_html=True)  # Display board interactively

        # Button to go forward one move
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Next Move"):
                if st.session_state.current_move < len(moves):
                    # Make the move
                    board.push(chess.Move.from_uci(moves[st.session_state.current_move]))
                    st.session_state.current_move += 1
                    st.session_state.board = board  # Save the board state
                else:
                    st.warning("No more moves to show.")

        # Button to go back one move
        with col2:
            if st.button("Previous Move"):
                if st.session_state.current_move > 0:
                    # Undo the last move
                    st.session_state.current_move -= 1
                    board.pop()
                    st.session_state.board = board  # Save the board state
                else:
                    st.warning("No previous moves to show.")

        # Remove the temporary PGN file
        os.remove("temp_game.pgn")

if __name__ == "__main__":
    main()
