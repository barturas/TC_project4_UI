import keyboard

def on_press(key):
    try:
        print(f'Alphanumeric key pressed: {key.char}')
    except AttributeError:
        print(f'Special key pressed: {key}')

keyboard.on_press(on_press)
keyboard.wait('esc')
