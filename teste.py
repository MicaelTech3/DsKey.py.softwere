# Exemplo conceitual com CustomTkinter
import customtkinter as ctk
import tkinter as ctk 

root = ctk.CTk()
root.geometry("800x600")



    def sel():
        selection = "Selecione o conteúdo " + str(var.get())
        label.config(text = selection)

    root = Tk()
    var = IntVar()
    R1 = Radiobutton(root, text="Python4noobs", variable=var, value=1,
                    command=sel)
    R1.pack( anchor = W )

    R2 = Radiobutton(root, text="Cpp4noobs", variable=var, value=2,
                    command=sel)
    R2.pack( anchor = W )

    R3 = Radiobutton(root, text="PHP4noobs", variable=var, value=3,
                    command=sel)
    R3.pack( anchor = W)

    label = Label(root)
    label.pack()
    root.mainloop()
