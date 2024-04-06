from tkinter import *
from dataclasses import dataclass, field

@dataclass
class Data_variable():
    print_name: str
    att_name: str
    att_type: type
    num_components: int

class Data_frame():
    def __init__(self, root:Frame, variables:Data_variable) -> None:
        frame = Frame(root, padx = 5, pady = 5)

        list_frame = Frame(frame)
        list_frame.grid(row = 0, column = 0, sticky=(N, E, W, S), padx=1, pady=1)
        scroll = Scrollbar(list_frame)
        scroll.pack(side = RIGHT, fill = Y)
        listbox = Listbox(list_frame, yscrollcommand = scroll.set)
        listbox.pack(side=LEFT, fill = BOTH, expand = YES)
        scroll.config(command=listbox.yview)

        data_frame = Frame(frame)
        data_frame.grid(row = 1, column = 0, sticky=(S, E, W), padx=1, pady=1, columnspan=2)
        self.entries = {}
        rows = 0
        for variable in variables:
            label = Label(data_frame, text=variable.print_name)
            label.grid(row = rows, column= 0)
            entry = Entry(data_frame)
            entry.grid(row = rows, column= 1, sticky="we")
            self.entries[variable.att_name] = entry
            rows += 1
        btn_discard = Button(data_frame, text="Discard", height = 1)
        btn_discard.grid(row = rows, column= 0)
        btn_apply = Button(data_frame, text="Apply", height = 1)
        btn_apply.grid(row = rows, column= 1, sticky="we")

        data_frame.columnconfigure(0, weight=1)
        data_frame.columnconfigure(1, weight=100)

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=100)
        frame.rowconfigure(1, weight=1)

        self.frame = frame
        self.focus = listbox
        self.listbox = listbox
        self.btn_apply = btn_apply
        self.btn_discard = btn_discard
        self.variables = variables

    def update_data_ui(self, data):
        for variable, entry in zip(self.variables, self.entries):
            self.entries[entry].delete(0, END)
            if variable.num_components == 1:
                self.entries[entry].insert(0, getattr(data, variable.att_name))
            else:
                array_data = getattr(data, variable.att_name)
                text = ""
                for i in range(variable.num_components):
                    text += str(array_data[i]) + " "
                self.entries[entry].insert(0, text)

    def update_data_bsp(self, data):
        for variable, entry in zip(self.variables, self.entries):
            var_t = variable.att_type
            if var_t is str:
                setattr(data, variable.att_name, bytes(self.entries[entry].get(), "latin-1"))
                continue
            if variable.num_components == 1:
                setattr(data, variable.att_name, var_t(self.entries[entry].get()))
            else:
                array_data = self.entries[entry].get().split(" ", variable.num_components-1)
                setattr(data, variable.att_name, tuple(map(var_t, array_data)))

if __name__ == "__main__":
	print("Please run 'main.py'")