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
            return True
        else:
            return False
        
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

cx, cy = 0, 0
class LabeledField(ColumnObject):
    def __init__(self, parent, y, column, column_span, num_columns, label, value):
        super().__init__(parent, y, column, column_span, num_columns)
        self.label = label
        self.value = value
        self.ll = len(label) + 2
        self.vx = self.x + self.ll
        self.vw = self.w - self.ll
        
    def draw(self, window, focus=False):
        global focused, cx, cy
        focus = focus or focused == self
        if(focus):
            window.addstr(self.y, self.x, self.label + ':')
        else:
            window.addstr(self.y, self.x, self.label.replace('[', '').replace(']','') + ':')
        window.addstr(self.y, self.vx, pad(self.value, self.vw), curses.A_REVERSE)
        if(focused == self):
            cx = self.vx + (self.vw + len(self.value)) // 2 + self.offset
            cy = self.y
                    
    def start_editing(self):
        global focused
        self.prev_foc = focused
        self.offset = 0
        focus_on(self)
    
    def finish_editing(self):
        focus_on(self.prev_foc)
        
    def focus(self):
        curses.curs_set(2)
        super().focus()
        
    def blur(self):
        curses.curs_set(0)
        super().blur()
        
    def key_pressed(self, key_code):
        global focused
        if(super().key_pressed(key_code)):
            return True
        if(focused == self):
            if(key_code == 'KEY_BACKSPACE'):
                if(len(self.value) > 0):
                    self.value = self.value[:-1+self.offset] + self.value[len(self.value)+self.offset:]
            elif(key_code == 'KEY_LEFT'):
                if(-self.offset < len(self.value)):
                    self.offset -= 1
            elif(key_code == 'KEY_RIGHT'):
                if(self.offset < 0):
                    self.offset += 1
            elif(key_code == 'KEY_HOME'):
                self.offset = -len(self.value)
            elif(key_code == 'KEY_END'):
                self.offset = 0
            elif(key_code == '\n'):
                self.finish_editing()
            else:
                i = len(self.value) + self.offset
                self.value = self.value[:i] + key_code + self.value[i:]
            return True
        return False
        
class Label(ColumnObject):
    def __init__(self, parent, y, column, column_span, num_columns, text):
        super().__init__(parent, y, column, column_span, num_columns)
        self.text = text
    
    def draw(self, window, focus=False):
        global focused
        focus = focus or focused == self
        if(focus):
            window.addstr(self.y, self.x, self.text)
        else:
            window.addstr(self.y, self.x, self.text.replace('[', '').replace(']',''))
        
class ScrollBox(ColumnObject):
    def __init__(self, parent, y, height, column, column_span, num_columns, label, values):
        super().__init__(parent, y, column, column_span, num_columns)
        self.h = height
        self.index = 0
        self.scroll = 0
        self.label = label
        self.values = values
        self.on_scroll = lambda scroll_box: 0
        
    def draw(self, window, focus=False):
        global focused
        focus = focus or focused == self
        vl = len(self.values)
        if(self.scroll > vl - self.h):
            self.scroll = vl - self.h
        if(self.scroll < 0):
            self.scroll = 0
        iw = self.w - 1
        for i in range(0, min(self.h, vl)):
            window.addstr(self.y + i + 1, self.x, pad(self.values[i+self.scroll], iw), [curses.A_REVERSE, curses.A_NORMAL][i+self.scroll==self.index])
        window.addstr(self.y, self.x, pad(self.label, self.w), curses.A_REVERSE)
        window.addstr(self.y+1, self.x+self.w-1, '^', [curses.A_NORMAL, curses.A_REVERSE][self.scroll>0])
        window.addstr(self.y+self.h, self.x+self.w-1, 'v', [curses.A_NORMAL, curses.A_REVERSE][self.scroll<vl-self.h])
    
    def scroll_to(self, index):
        if(type(index) != int):
            try:
                index = self.values.index(index)
            except:
                return
        if(index < 0):
            index = 0
        if(index > len(self.values)-1):
            index = len(self.values)-1
        if(self.scroll > index):
            self.scroll = index
        if(self.scroll < index - self.h + 1):
            self.scroll = index - self.h + 1
        self.index = index
        self.on_scroll(self)
        
    def get_selected(self):
        return self.values[self.index]
    
    def key_pressed(self, key_code):
        super().key_pressed(key_code)
        if(key_code == 'KEY_DOWN'):
            self.scroll_to(self.index + 1)
        elif(key_code == 'KEY_UP'):
            self.scroll_to(self.index - 1)
        
class View(CursesObject):
    def __init__(self, parent=None, y=0, x=0, height=0, width=0):
        super().__init__(parent)
        self.children = []
        if(parent is not None):
            x += parent.x
            y += parent.y
        self.x, self.y = x, y
        self.w, self.h = width, height
        if(self.h == 0):
            if(parent is None):
                self.h = curses.LINES - y
            else:
                self.h = parent.h - y
        if(self.w == 0):
            if(parent is None):
                self.w = curses.COLS - x
            else:
                self.w = parent.w - x
        if(parent is None):
            self.window = defaultWindow.subwin(self.h, self.w, self.y, self.x)
        else:
            self.window = parent.window.subwin(self.h, self.w, self.y, self.x)
    
    def draw(self, window=None, focus=False):
        global focused
        focus = focus or focused == self
        for child in self.children:
            if(child.visible):
                child.draw(self.window, focus)
    
    def key_pressed(self, key_code):
        if(not super().key_pressed(key_code)):
            for child in self.children:
                if(child.key_pressed(key_code)):
                    return True
            return False
        return True
            
class MultiView(View):
    def __init__(self, parent=None, height=0, width=0, y=0, x=0):
        super().__init__(parent, height, width, y, x)
        self.shown = None
    
    def draw(self, window=None, focus=False):
        global focused
        focus = focus or focused == self
        if(self.shown is not None):
            self.shown.draw(self.window, focus)
            
    def change_shown(self, child):
        self.shown = child
        
    def clear_shown(self):
        self.shown = None
        
focused = None

def focus_on(object):
    global focused
    if(focused is not None):
        focused.blur()
    focused = object
    object.focus()
    
def clear_focus():
    global focused
    if(focused is not None):
        focused.blur()
    focused = None

def construct_method_view(parent, method_box, return_focus):
    method_view = View(parent)
    methods = ScrollBox(method_view, 0, 7, 0, 1, 3, 'METHODS', ('[D]ELETE', '[G]ET', '[H]EAD', '[O]PTIONS', 'P[A]TCH', '[P]OST', 'PU[T]'))
    methods.scroll_to(1)
    def set_method(scroll_box):
        method_box.value = methods.get_selected().replace('[','').replace(']','')
    methods.on_scroll = set_method
    def select(index):
        def callback(scroll_box):
            scroll_box.scroll_to(index)
            return_focus()
        return callback
    methods.on_key['d'] = select(0)
    methods.on_key['g'] = select(1)
    methods.on_key['h'] = select(2)
    methods.on_key['o'] = select(3)
    methods.on_key['a'] = select(4)
    methods.on_key['p'] = select(5)
    methods.on_key['t'] = select(6)
    methods.on_key['m'] = lambda e: return_focus()
    methods.on_key['\n'] = lambda e: return_focus()
    return method_view
   
def main(screen):
    global defaultWindow, focused, cx, cy
    defaultWindow = screen
    
    w, h = curses.COLS, curses.LINES
    
    root_view = View()
    
    home_view = View(root_view)
    method = LabeledField(home_view, 0, 0, 1, 3, '[M]ETHOD', 'GET')
    url = LabeledField(home_view, 0, 1, 2, 3, '[U]RL', 'https://www.google.com')
    headers = LabeledField(home_view, 2, 0, 1, 3, '[H]EADERS', '+0 ~0 -0')
    query = LabeledField(home_view, 2, 1, 1, 3, '[Q]UERY', '0 parameters')
    body = LabeledField(home_view, 2, 2, 1, 3, '[B]ODY', 'N/A')
    commands = Label(home_view, 4, 0, 1, 1, 'E[X]ECUTE')
    
    sub_view = MultiView(root_view, 6)
    def return_focus():
        sub_view.clear_shown()
        focus_on(home_view)
    def open(subview):
        sub_view.change_shown(subview)
        focus_on(subview)
        
    method_view = construct_method_view(sub_view, method, return_focus)
    
    home_view.on_key['m'] = lambda e: open(method_view)
    home_view.on_key['u'] = lambda e: url.start_editing()
    
    focus_on(home_view)
    curses.curs_set(0)
    
    while True:
        screen.clear()
        root_view.draw()
        screen.move(cy, cx)
        screen.refresh()
        #curses.flash()
        focused.key_pressed(screen.getkey())
        #method.value = screen.getkey()
    
# Sets up curses, runs main, then stops curses, so that no matter how the program stops, we can still use the terminal properly.
curses.wrapper(main)
