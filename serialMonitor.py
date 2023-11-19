from time import sleep
from random import random
import flet as ft
import datetime
from faker import Faker
from threading import Thread

from serialController import SerialController

class Message:
    message = ""
    time = ""


    def __init__(self, message: str, ) -> None:
        self.message = message
        self.time = datetime.datetime.now().strftime("%H:%M")

    
class Monitor:
    ftPage = None
    displaySetup = True
    serialCtl = None
    port = ""

    massagesView = None

    


    def __init__(self) -> None:
        self.serialCtl = SerialController()


        self.massagesView =  ft.ListView(
            expand=True,
            spacing=10,
            auto_scroll=True)
        
    def _get_msg_system(self, message : Message) -> ft.Row:
        row = ft.Row([ft.Text(message.time), ft.Text(message.message)], spacing=10, alignment=ft.MainAxisAlignment.CENTER)

        # container = ft.Container(content=row, padding=10, border_radius=5, bgcolor=ft.colors.BLUE_GREY_200, shadow=ft.BoxShadow(
        #     spread_radius=1,
        #     blur_radius=0,
        #     color=ft.colors.BLUE_GREY_300,
        #     offset=ft.Offset(0, 0),
        #     blur_style=ft.ShadowBlurStyle.OUTER,
        # ))

        return row

        


    def get_message_element(self, message : Message) -> ft.Row:
        return self._get_msg_system(message)

    def add_message(self, message : Message) -> None:
        self.massagesView.controls.append(self.get_message_element(message))
        self.ftPage.update()

    def _run_receive(self) -> None:
        while True:
            message = self.serialCtl.receive()
            if(message is not None):
                self.ftPage.pubsub.send_all(Message(f"{message[0]}[{','.join(message[1])}]"))
            sleep(0.1)

    def _get_setup_view(self) -> ft.View:
        portList = [ft.dropdown.Option(p) for p in self.serialCtl.get_ports()]

        if(len(portList) == 0):
            self.show_no_port_banner()
            portList = [ft.dropdown.Option("No Ports Found")]
        else:
            self.close_banner(None)

        portDD = ft.Dropdown( width=300,options=portList, value=portList[0])
        baudRate = ft.Dropdown( width=300,options=[ft.dropdown.Option("300"),
                                                   ft.dropdown.Option("600"), 
                                                   ft.dropdown.Option("750"),
                                                   ft.dropdown.Option("1200"),
                                                   ft.dropdown.Option("2400"), 
                                                   ft.dropdown.Option("4800"),
                                                   ft.dropdown.Option("9600"),
                                                   ft.dropdown.Option("19200"), 
                                                   ft.dropdown.Option("31250"),
                                                   ft.dropdown.Option("38400"),
                                                   ft.dropdown.Option("57600"), 
                                                   ft.dropdown.Option("115200"),
                                                   ft.dropdown.Option("230400"),
                                                   ft.dropdown.Option("250000"), 
                                                   ft.dropdown.Option("500000"),
                                                   ft.dropdown.Option("1000000"),
                                                   ft.dropdown.Option("2000000")], 
                                                   value=ft.dropdown.Option("9600"))
        baudRate.value = "115200"
        
        return ft.View(
            "/",
            [
                ft.Text("Select Port"),
                ft.AppBar(title=ft.Text("Setup"), bgcolor=ft.colors.SURFACE_VARIANT),
                portDD,
                ft.Text("Baud Rate"),
                baudRate,
                ft.ElevatedButton("Start", on_click=lambda e : self.submitSetup(portDD.value, baudRate.value)),
            ],
        )
    
    def send_message(self, message : str) -> None:
        self.serialCtl.send(message + "\n")
        self.ftPage.pubsub.send_all(Message(message))
        
    def _get_chat_view(self) -> ft.View:


        new_message = ft.TextField(
            hint_text="Write a message...",
            autofocus=True,
            shift_enter=True,
            min_lines=1,
            max_lines=5,
            filled=True,
            expand=True,
            on_submit=lambda e : self.send_message(new_message.value),
            )
        
        def submit(e):
            self.send_message(new_message.value)
            new_message.value = ""
            new_message.focus()
            self.ftPage.update()

        new_message.on_submit = submit

        chatField = ft.Row([new_message, ft.IconButton(icon=ft.icons.SEND_ROUNDED,tooltip="Send message",on_click=submit),], spacing=10)


        view = ft.View(
            "/",
            [
                ft.AppBar(title=ft.Text("Chat"), bgcolor=ft.colors.SURFACE_VARIANT),
                ft.Container(
                    content=self.massagesView,
                    border=ft.border.all(1, ft.colors.OUTLINE),
                    border_radius=5,
                    padding=10,
                    expand=True,
                ),
                chatField,                
            ],
            )
        
        # view.horizontal_alignment = "stretch"
        # view.scroll = "always"
        return view


    def route_change(self, route) -> None:
        self.ftPage.views.clear()
        if(self.displaySetup):
            self.ftPage.views.append(self._get_setup_view())
        else:
            self.ftPage.views.append(self._get_chat_view())
       
        self.ftPage.update()


    def ui(self, page: ft.Page) -> None:
        self.ftPage = page
        page.theme_mode = ft.ThemeMode.DARK
        page.title = "Serial Monitor"
        page.horizontal_alignment = "stretch"
        page.pubsub.subscribe(self.add_message)
        self.ftPage.banner = ft.Banner( content=ft.Text("Loading...",color=ft.colors.BLACK87),actions=[ft.TextButton("Reload", on_click=self._reload_setup)])
        self.ftPage.banner.open = False


        page.on_route_change = self.route_change
        page.on_view_pop = self.view_pop
        page.go(page.route)

        

        # fake = Faker()
        # for _ in range(1):
        #     random_message = fake.text()
        #     random_name = fake.name()
        #     self.add_message(Message(random_message, random_name))

    def view_pop(self, view : ft.View) -> None:
        self.ftPage.views.pop()
        top_view = self.ftPage.views[-1]
        self.ftPage.go(top_view.route)

    def show_invalid_address_banner(self) -> None:
        self.ftPage.banner = ft.Banner(
        bgcolor=ft.colors.RED_100,
        leading=ft.Icon(ft.icons.WARNING_AMBER_SHARP, color=ft.colors.BLACK87, size=40),
        content=ft.Text(
            "Invalid Address, your address has to be set between 0 and 254",
            color=ft.colors.BLACK87,
        ),
        actions=[
            ft.TextButton("Ok", on_click=self.close_banner),
        ],
        )
        
        self.ftPage.banner.open = True
        self.ftPage.update()

    def show_invalid_port_banner(self) -> None:
        self.ftPage.banner = ft.Banner(
        bgcolor=ft.colors.RED_100,
        leading=ft.Icon(ft.icons.WARNING_AMBER_SHARP, color=ft.colors.BLACK87, size=40),
        content=ft.Text(
            "Invalid Port, please select a port",
            color=ft.colors.BLACK87,
        ),
        actions=[
            ft.TextButton("Ok", on_click=self.close_banner),
        ],
        )
        
        self.ftPage.banner.open = True
        self.ftPage.update()

    def _reload_setup(self,e ) -> None:
        self.ftPage.views.clear()
        self.ftPage.views.append(self._get_setup_view())
        self.ftPage.update()
        

    def show_no_port_banner(self) -> None:
        self.ftPage.banner = ft.Banner(
        bgcolor=ft.colors.RED_100,
        leading=ft.Icon(ft.icons.WARNING_AMBER_SHARP, color=ft.colors.BLACK87, size=40),
        content=ft.Text(
            "No Ports Found, please connect a device",
            color=ft.colors.BLACK87,
        ),
        actions=[
            ft.TextButton("Reload", on_click=self._reload_setup),
        ],
        )
        
        self.ftPage.banner.open = True
        self.ftPage.update()
        
    def close_banner(self, e : ft.event):
        self.ftPage.banner.open = False
        self.ftPage.update()

    def submitSetup(self, port : str, baudRate : str) -> None:
       


        if(port == "" or port is None or port == "No Ports Found"):
            self.show_invalid_port_banner()
            return


        self.displaySetup = False
        self.port = port
        self.serialCtl.start(port, baudRate)
        self.ftPage.go("/no_route")
        
        # self.ftPage.views.clear()
        # self.ftPage.views.append(self._get_chat_view())
        # self.ftPage.update()

        self.recThread = Thread(target=self._run_receive)
        self.recThread.start()




def main():
    print("Starting")
    chat = Monitor()
    ft.app(target=chat.ui)



if __name__ == "__main__":
    main()




