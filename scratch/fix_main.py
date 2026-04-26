import sys

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('selected_level = 1\ngame_state = "title"\nplay_music("title.mid", loops=-1)\n\nwhile True:')

if idx != -1:
    before = content[:idx]
    after = content[idx:]
    lines = after.split('\n')
    
    new_after = 'def run_game():\n    global selected_level, game_state\n'
    for line in lines:
        if line == '':
            new_after += '\n'
        else:
            new_after += '    ' + line + '\n'
            
    new_after += '\nif __name__ == "__main__":\n    run_game()\n'
    
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(before + new_after)
    print('Fixed main.py')
else:
    print('Pattern not found')
