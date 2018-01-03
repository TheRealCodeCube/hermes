import curses
   
def pad(text, width):
    l = len(text)
    if(l > width):
        return text[:width-3] + '...'
    elif(l < width):
        gap = width - l
        return (' ' * (gap // 2)) + text + (' ' * ((gap + 1) // 2))
    else:
        return text
    
def x(column, num_columns):
    return int((column * curses.COLS + 0.5) // num_columns)
   
class LabeledField:
    def __init__(self, window, y, column, column_span, num_columns, label, value):
        self.window = window
        self.y = y
        self.label = label
        self.value = value
        self.lx = x(column, num_columns)
        self.ll = len(label) + 2
        self.vx = self.lx + self.ll
        self.vw = x(column + column_span, num_columns) - x(column, num_columns) - self.ll - 1
        
    def draw(self):
        self.window.addstr(self.y, self.lx, self.label + ':')
        self.window.addstr(self.y, self.vx, pad(self.value, self.vw), curses.A_REVERSE)        
   
def main(screen):
    screen.clear()
    
    w, h = curses.COLS, curses.LINES
    
    method = LabeledField(screen, 0, 0, 1, 3, '[M]ETHOD', 'GET')
    url = LabeledField(screen, 0, 1, 2, 3, '[U]RL', 'https://www.google.com')
    headers = LabeledField(screen, 2, 0, 1, 3, '[H]EADERS', '+0 ~0 -0')
    query = LabeledField(screen, 2, 1, 1, 3, '[Q]UERY', '0 parameters')
    body = LabeledField(screen, 2, 2, 1, 3, '[B]ODY', 'N/A')
    
    method.draw()
    url.draw()
    headers.draw()
    query.draw()
    body.draw()
    
    screen.move(h-1, w-1) #Move that obnoxious blinking cursor out of the way
    screen.refresh()
    screen.getkey()
    
# Sets up curses, runs main, then stops curses, so that no matter how the program stops, we can still use the terminal properly.
curses.wrapper(main)
