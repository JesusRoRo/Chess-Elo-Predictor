import chess

# Define material values
MATERIAL_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0
}

# Center squares 
CENTER_SQUARES = [chess.D4, chess.E4, chess.D5, chess.E5]

# Pawn Structure 
PAWN_STRUCTURE_SCORES = {
    1: -0.5,  # Pawn on the 1st rank
    2: 0,     # Pawn on the 2nd rank
    3: 0.5,   # Pawn on the 3rd rank
    4: 1,     # Pawn on the 4th rank
    5: 1,     # Pawn on the 5th rank
    6: 0.5,   # Pawn on the 6th rank
    7: 0,     # Pawn on the 7th rank
    8: -0.5   # Pawn on the 8th rank
}

# Evaluate material: sum of piece values
def evaluate_material(board):
    white_material = 0
    black_material = 0

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None:
            if piece.color == chess.WHITE:
                white_material += MATERIAL_VALUES.get(piece.piece_type, 0)
            else:
                black_material += MATERIAL_VALUES.get(piece.piece_type, 0)
    
    return white_material, black_material

# Evaluate piece activity
def evaluate_piece_activity(board):
    white_activity = 0
    black_activity = 0

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None:
            continue

        # Piece activity
        if piece.color == chess.WHITE:
            if square in CENTER_SQUARES:
                white_activity += 1
            elif piece.piece_type in [chess.KNIGHT, chess.BISHOP] and square in [chess.C3, chess.F3, chess.C4, chess.F4]:
                white_activity += 0.5
        elif piece.color == chess.BLACK:
            if square in CENTER_SQUARES:
                black_activity += 1
            elif piece.piece_type in [chess.KNIGHT, chess.BISHOP] and square in [chess.C6, chess.F6, chess.C5, chess.F5]:
                black_activity += 0.5
    
    return white_activity, black_activity

# Evaluate pawn structure
def evaluate_pawn_structure(board):
    white_pawn_score = 0
    black_pawn_score = 0

    for square in chess.SQUARES:
        piece = board.piece_at(square)

        if piece is None or piece.piece_type != chess.PAWN:
            continue

        # Evaluate pawns based on their rank
        if piece.color == chess.WHITE:
            white_pawn_score += PAWN_STRUCTURE_SCORES.get(chess.square_rank(square), 0)
        elif piece.color == chess.BLACK:
            black_pawn_score += PAWN_STRUCTURE_SCORES.get(chess.square_rank(square), 0)
    
    return white_pawn_score, black_pawn_score

# Evaluate king safety
def evaluate_king_safety(board):
    white_king_safety = 0
    black_king_safety = 0

    if board.king(chess.WHITE) is not None:
        white_king_square = board.king(chess.WHITE)
        # If the white king is in a safe position 
        if chess.square_file(white_king_square) in [chess.C1, chess.G1] and chess.square_rank(white_king_square) == 1:
            white_king_safety += 1  # KingCastled

    if board.king(chess.BLACK) is not None:
        black_king_square = board.king(chess.BLACK)
        # If the black king is in a safe position 
        if chess.square_file(black_king_square) in [chess.C8, chess.G8] and chess.square_rank(black_king_square) == 8:
            black_king_safety += 1  # KingCastled


    return white_king_safety, black_king_safety

# Evaluate position
def evaluate_position(board):
    white_activity, black_activity = evaluate_piece_activity(board)
    white_pawn_score, black_pawn_score = evaluate_pawn_structure(board)
    white_king_safety, black_king_safety = evaluate_king_safety(board)

    # Combine all the positional evaluations
    white_position = white_activity + white_pawn_score + white_king_safety
    black_position = black_activity + black_pawn_score + black_king_safety
    
    return white_position, black_position

# Main function to evaluate the performance based on both material and position after each move
def evaluate_performance(game):
    # Initialize scores
    white_score = 0
    black_score = 0
    total_score = 0

    #Initialize board
    board = game.board()

    # Iterate through all moves in the game
    for move in game.mainline_moves():
        # Check if the move is legal
        if board.is_legal(move):
            board.push(move)  # Apply the legal move

            # Evaluate the material and position after the move
            white_material, black_material = evaluate_material(board)
            white_position, black_position = evaluate_position(board)

            # Combine material and positional evaluations
            white_move_score = white_material + white_position
            black_move_score = black_material + black_position

            # Update cumulative scores
            white_score += white_move_score
            black_score += black_move_score
            total_score = white_score + black_score
        else:
            print(f"Illegal move encountered: {move}, skipping.")

    # Get a percentage at the end of the game
    if total_score == 0:
        return 50.0, 50.0  # Draw gives equal
    
    white_performance = (white_score / total_score) * 100
    black_performance = (black_score / total_score) * 100
    
    return white_performance, black_performance