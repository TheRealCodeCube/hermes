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
        if(key_code in self.on_key.keys()):
            self.on_key[key_code](self)
        
    def focus(self):
        self.on_focus(self)
        
    def blur(self):
        self.on_blur(self)
        
    def show(self):
        self.visible = True
        
    def hide(self):
        self.visible = False

class ColumnObject(CursesObject):
    def __init__(self, parent, y, column, column_span, num_columns):
        super().__init__(parent)
        parent.children.append(self)
        self.y = y
        self.x = x(column, num_columns)
        self.w = x(column + column_span, num_columns) - x(column, num_columns) - 1

class LabeledField(ColumnObject):
    def __init__(self, parent, y, column, column_span, num_columns, label, value):
        super().__init__(parent, y, column, column_span, num_columns)
        self.label = label
        self.value = value
        self.ll = len(label) + 2
        self.vx = self.x + self.ll
        self.vw = self.w - self.ll
        
    def draw(self, window):
        window.addstr(self.y, self.x, self.label + ':')
        window.addstr(self.y, self.vx, pad(self.value, self.vw), curses.A_REVERSE)
        
    def focus(self):
        curses.curs_set(2)
        super().focus()
        
    def blur(self):
        curses.curs_set(0)
        super().blur()
        
class ScrollBox(ColumnObject):
    def __init__(self, parent, y, height, column, column_span, num_columns, values):
        super().__init__(parent, y, column, column_span, num_columns)
        self.h = height
        self.index = 0
        self.scroll = 0
        self.values = values
        
    def draw(self, window):
        vl = len(self.values)
        if(self.scroll > vl - self.h):
            self.scroll = vl - self.h
        if(self.scroll < 0):
            self.scroll = 0
        iw = self.w
        if(vl > self.h):
            iw -= 1
        for i in range(0, min(self.h, vl)):
            window.addstr(self.y + i, self.x, pad(self.values[i+self.scroll], iw), [curses.A_NORMAL, curses.A_REVERSE][i+self.scroll==self.index])
        
class View(CursesObject):
    def __init__(self, parent=None, y=0, x=0, height=0, width=0):
        super().__init__(parent)
        self.children = []
        self.x, self.y = x, y
        self.w, self.h = width, height
        if(self.h == 0):
            if(parent is None):
                self.h = curses.LINES
            else:
                self.h = parent.h - y
        if(self.w == 0):
            if(parent is None):
                self.w = curses.COLS
            else:
                self.w = parent.w - x
        if(parent is None):
            self.window = defaultWindow.subwin(self.h, self.w, self.y, self.x)
        else:
            self.window = parent.window.subwin(self.h, self.w, self.y, self.x)
    
    def draw(self, window=None):
        for child in self.children:
            if(child.visible):
                child.draw(self.window)
            
class MultiView(View):
    def __init__(self, parent=None, height=0, width=0, y=0, x=0):
        super().__init__(parent, height, width, y, x)
        self.shown = None
    
    def draw(self, window=None):
        if(self.shown is not None):
            self.shown.draw(self.window)
            
    def change_shown(self, child):
        self.shown = child
        
    def clear_shown(self):
        self.shown = None
        
focused = None

def focus_on(object):
    global focused
    focused = object
    object.focus()
    
def clear_focus():
    global focused
    if(focused is not None):
        focused.blur()
    focused = None

def construct_method_view(parent):
    method_view = View(parent)
    methods = ScrollBox(method_view, 0, 5, 0, 1, 1, ('1', '2', '3', '4', '5'))
    return method_view    
   
def main(screen):
    global defaultWindow, focused
    defaultWindow = screen
    
    w, h = curses.COLS, curses.LINES
    
    root_view = View()
    
    home_view = View(root_view)
    method = LabeledField(home_view, 0, 0, 1, 3, '[M]ETHOD', 'GET')
    url = LabeledField(home_view, 0, 1, 2, 3, '[U]RL', 'https://www.google.com')
    headers = LabeledField(home_view, 2, 0, 1, 3, '[H]EADERS', '+0 ~0 -0')
    query = LabeledField(home_view, 2, 1, 1, 3, '[Q]UERY', '0 parameters')
    body = LabeledField(home_view, 2, 2, 1, 3, '[B]ODY', 'N/A')
    
    sub_view = MultiView(root_view, 4, 0)
    method_view = construct_method_view(sub_view)
    sub_view.change_shown(method_view)
    
    focus_on(home_view)
    
    while True:
        screen.clear()
        curses.curs_set(0)
        root_view.draw()
        screen.refresh()
        curses.flash()
        focused.key_pressed(screen.getkey())
        #method.value = screen.getkey()
    
# Sets up curses, runs main, then stops curses, so that no matter how the program stops, we can still use the terminal properly.
curses.wrapper(main)
