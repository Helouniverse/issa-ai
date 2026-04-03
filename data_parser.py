import json

def load_and_group_conversations(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    training_examples = []
    
    for conv_data in data:
        conversation = conv_data.get('conversation', [])
        
        # Group messages into alternating sequences of 'in' and 'out'
        sequences = []
        current_sequence = []
        current_direction = None
        
        for msg in conversation:
            direction = msg['direction']
            text = msg.get('text', '')
            
            if current_direction is None:
                current_direction = direction
                current_sequence.append(text)
            elif direction == current_direction:
                current_sequence.append(text)
            else:
                sequences.append({
                    'direction': current_direction,
                    'text': '\n'.join(current_sequence)
                })
                current_direction = direction
                current_sequence = [text]
                
        if current_sequence:
            sequences.append({
                'direction': current_direction,
                'text': '\n'.join(current_sequence)
            })
            
        # Construct the pairs
        chat_history = []
        i = 0
        while i < len(sequences):
            if sequences[i]['direction'] == 'in':
                client_seq = sequences[i]['text']
                if i + 1 < len(sequences) and sequences[i+1]['direction'] == 'out':
                    consultant_reply = sequences[i+1]['text']
                    
                    training_examples.append({
                        'chat_history': list(chat_history),
                        'client_sequence': client_seq,
                        'consultant_reply': consultant_reply
                    })
                    
                    chat_history.append({'role': 'client', 'content': client_seq})
                    chat_history.append({'role': 'consultant', 'content': consultant_reply})
                    i += 2  # skip the out sequence since it's consumed
                else:
                    chat_history.append({'role': 'client', 'content': client_seq})
                    i += 1
            else:
                chat_history.append({'role': 'consultant', 'content': sequences[i]['text']})
                i += 1
                
    return training_examples

if __name__ == "__main__":
    examples = load_and_group_conversations('conversations.json')
    print(f"Total training examples extracted: {len(examples)}\n")
    if examples:
        # Print a few samples to verify
        for idx in range(min(2, len(examples))):
            sample = examples[idx]
            print(f"========== SAMPLE EXAMPLE {idx+1} ==========")
            print("--- Preceding Chat History ---")
            if not sample['chat_history']:
                print("(No prior history)")
            for h in sample['chat_history']:
                print(f"[{h['role'].upper()}]: {h['content']}")
            print("\n--- Client Sequence ---")
            print(sample['client_sequence'])
            print("\n--- Consultant Reply ---")
            print(sample['consultant_reply'])
            print("=========================================\n")
