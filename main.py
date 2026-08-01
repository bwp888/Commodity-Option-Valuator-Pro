import customtkinter as ctk

from ui.styles import init_theme


class App(ctk.CTk):

    def __init__(self):

        super().__init__()

        self.title("Commodity Option Valuator Pro")

        self.geometry("1600x900")

        self.minsize(1400, 850)

        self.create_ui()

    def create_ui(self):

        title = ctk.CTkLabel(
            self,
            text="Commodity Option Valuator Pro",
            font=("微软雅黑", 28, "bold")
        )

        title.pack(pady=20)

        sub = ctk.CTkLabel(
            self,
            text="商品期权智能估值分析系统",
            font=("微软雅黑", 18)
        )

        sub.pack()

        version = ctk.CTkLabel(
            self,
            text="Version 0.1.0",
            font=("微软雅黑", 14)
        )

        version.pack(pady=5)


if __name__ == "__main__":

    init_theme()

    app = App()

    app.mainloop()