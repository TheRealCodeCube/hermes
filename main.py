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
    return int((column * (curses.COLS+1) + 0.5) // num_columns)
   
class CursesObject:
    def __init__(self, parent=None):
        self.parent = parent
        if(parent is not None):
            self.parent.children.append(self)
        self.visible = True
        self.on_key = {}
        self.on_focus = lambda object: 0
        self.on_blur = lambda object: 0
        
    def key_pressed(self, key_code):
        if(key_code in self.on_key.__keys__()):
            self.on_key[key_code](self)
        
    def focus(self):
        self.on_focus()
        
    def blur(self):
        self.on_blur()
        
    def show(self):
        self.visible = True
        
    def hide(self):
        self.visible = False

class LabeledField(CursesObject):
    def __init__(self, parent, y, column, column_span, num_columns, label, value):
        super().__init__(parent)
        parent.children.append(self)
        self.y = y
        self.label = label
        self.value = value
        self.lx = x(column, num_columns)
        self.ll = len(label) + 2
        self.vx = self.lx + self.ll
        self.vw = x(column + column_span, num_columns) - x(column, num_columns) - self.ll - 1
        
    def draw(self, window):
        window.addstr(self.y, self.lx, self.label + ':')
        window.addstr(self.y, self.vx, pad(self.value, self.vw), curses.A_REVERSE)
        
    def focus(self):
        curses.curs_set(2)
        super().focus()
        
    def blur(self):
        curses.curs_set(0)
        super().blur()
        
class View(CursesObject):
    def __init__(self, parent=None, height=0, width=0, y=0, x=0):
        super().__init__(parent)
        self.children = []
        self.x, self.y = x, y
        self.w, self.h = width, height
        if(self.w == 0):
            if(parent is None):
                self.w = curses.COLS
            else:
                self.w = parent.w
        if(self.h == 0):
            if(parent is None):
                self.h = curses.LINES
            else:
                self.h = parent.h
        if(parent is None):
            self.window = defaultWindow.subwin(self.h, self.w, self.y, self.x)
        else:
            self.window = parent.window.subwin(self.h, self.w, self.y, self.x)
        self.focus = None
    
    def draw(self, screen=None):
        for child in self.children:
            if(child.visible):
                child.draw(self.window)
            
    def focus_on(self, child):
        self.focus = child
        child.focus()
        
    def clear_focus(self):
        self.focus.blur()
        self.focus = None
        
    def key_pressed(self, key_code):
        if(self.focus is None):
            super().key_pressed(key_code)
        else:
            self.focus.key_pressed(key_code)
   
def main(screen):
    global defaultWindow
    defaultWindow = screen
    screen.clear()
    curses.curs_set(0)
    
    w, h = curses.COLS, curses.LINES
    
    root_view = View()
    home_view = View(root_view)
    
    method = LabeledField(home_view, 0, 0, 1, 3, '[M]ETHOD', 'GET')
    url = LabeledField(home_view, 0, 1, 2, 3, '[U]RL', 'https://www.google.com')
    headers = LabeledField(home_view, 2, 0, 1, 3, '[H]EADERS', '+0 ~0 -0')
    query = LabeledField(home_view, 2, 1, 1, 3, '[Q]UERY', '0 parameters')
    body = LabeledField(home_view, 2, 2, 1, 3, '[B]ODY', 'N/A')
    
    root_view.draw()
    
    #screen.move(h-1, w-1) #Move that obnoxious blinking cursor out of the way
    #home_view.window.refresh()
    screen.refresh()
    screen.getkey()
    
# Sets up curses, runs main, then stops curses, so that no matter how the program stops, we can still use the terminal properly.
curses.wrapper(main)
