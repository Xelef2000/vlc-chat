from time import sleep
from random import random
from threading import Thread
from queue import Queue
from queue import Empty
import flet as ft
import serial.tools.list_ports
import datetime
from faker import Faker




class SerialController:

    serialPort = "COM3"
    baudRate = 115200
    address = "AB"
    running = False


    def __init__(self) -> None:
        self.send_queue = Queue()
        self.receive_queue = Queue()

    
    def get_ports(self) -> list:
        ports = serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(ports):
            print("{}: {} [{}]".format(port, desc, hwid))
        return [p.device for p in ports]


    def start(self, serialPort: str, baudRate: int, address: str) -> None:
        self.serialPort = serialPort
        self.baudRate = baudRate
        self.address = address
        self.running = True
        self.thread = Thread(target=self._run)
        self.thread.start()
    
    def stop(self) -> None:
        self.running = False
        self.thread.join()

    def send(self, data: str) -> None:
        self.send_queue.put(data)

    def receive(self) -> str:
        try:
            return self.receive_queue.get(timeout=0.1)
        except Empty:
            return ""

    def _send_send_to_serial(self, data: str) -> None:
        print(f"Sending {data}")

    def _receive_from_serial(self) -> str:
        # randomly return a message 
        if random() < 0.1:
            return "Hello"
        else:
            return ""


    def _run(self) -> None:
        while self.running:
            try:
                data = self.send_queue.get(timeout=0.1)
            except Empty:
                pass
            else:
                self._send_to_serial(data)
            try:
                data = self._receive_from_serial()
            except Empty:
                pass
            else:
                if(data != ""):
                    self.receive_queue.put(data)
            sleep(random())



class Message:
    message = ""
    time = ""
    srcName = ""

    def __init__(self, message: str, srcName: str) -> None:
        self.message = message
        self.srcName = srcName
        self.time = datetime.datetime.now().strftime("%H:%M")
    
class Chat:
    ftPage = None
    displaySetup = True
    serialCtl = None
    name = ""
    address = ""
    port = ""



    def __init__(self) -> None:
        self.serialCtl = SerialController()

        self.mockMassages = []

        fake = Faker()
        for _ in range(100):
            random_message = fake.text()
            random_name = fake.name()
            self.mockMassages.append(Message(random_message, random_name))


    def _get_setup_view(self) -> ft.View:
        portDD = ft.Dropdown( width=300,options=[ft.dropdown.Option(p) for p in self.serialCtl.get_ports()])
        addressTF = ft.TextField(hint_text="AA", width=300)
        nameTF = ft.TextField(hint_text="", width=300)
        
        return ft.View(
            "/",
            [
                ft.AppBar(title=ft.Text("Setup"), bgcolor=ft.colors.SURFACE_VARIANT),
                portDD,
                ft.Text("Select Address"),
                addressTF,
                ft.Text("Name"),
                nameTF,
                ft.ElevatedButton("Submit", on_click=lambda e : self.submitSetup(addressTF.value, portDD.value, nameTF.value)),
            ],
        )
    
    def send_message(self, message : str) -> None:
        pass

    def _get_chat_view(self) -> ft.View:
        content = []
        
        for message in self.mockMassages:
            content.append(ft.Text(message.srcName))
            content.append(ft.Text(message.message))
            content.append(ft.Text(message.time))
            content.append(ft.Divider())

        new_message = ft.TextField(
            hint_text="Write a message...",
            autofocus=True,
            shift_enter=True,
            min_lines=1,
            max_lines=5,
            filled=True,
            expand=True,
            )

        chatField = ft.Row([new_message, ft.IconButton(icon=ft.icons.SEND_ROUNDED,tooltip="Send message",on_click=lambda e : self.send_message(new_message.value),),], spacing=10)


        massageList = ft.ListView(
            expand=True,
            spacing=10,
            auto_scroll=True,
            controls=content,
        )

        view = ft.View(
            "/",
            [
                ft.AppBar(title=ft.Text("Chat"), bgcolor=ft.colors.SURFACE_VARIANT),
                ft.Container(
                    content=massageList,
                    border=ft.border.all(1, ft.colors.OUTLINE),
                    border_radius=5,
                    padding=10,
                    expand=True,
                ),
                chatField,
                # ft.Container( content=ft.Column([, ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=10)),
                
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
        page.title = "VLC Chat"
        page.horizontal_alignment = "stretch"

        page.on_route_change = self.route_change
        page.on_view_pop = self.view_pop
        page.go(page.route)

    def view_pop(self, view : ft.View) -> None:
        self.ftPage.views.pop()
        top_view = self.ftPage.views[-1]
        self.ftPage.go(top_view.route)

    def show_invalid_address_banner(self) -> None:
        self.ftPage.banner = ft.Banner(
        bgcolor=ft.colors.RED_100,
        leading=ft.Icon(ft.icons.WARNING_AMBER_SHARP, color=ft.colors.BLACK87, size=40),
        content=ft.Text(
            "Invalid Address, your address has been set to be between 0 and 254",
            color=ft.colors.BLACK87,
        ),
        actions=[
            ft.TextButton("Ok", on_click=self.close_banner),
        ],
        )
        
        self.ftPage.banner.open = True
        self.ftPage.update()

        
    def close_banner(self, e : ft.event):
        self.ftPage.banner.open = False
        self.ftPage.update()

    def submitSetup(self, address : str, port : str, name: str ) -> None:
        if(len(name) == 0):
            name = "Anonymous"
        
        if(address == "" or int(address, 16) <= 0 or int(address, 16) > 254):
            self.show_invalid_address_banner()
            return


        self.displaySetup = False
        self.name = name
        self.address = address
        self.port = port
        self.serialCtl.start(port, 115200, address)
        self.ftPage.go("/chat")




def main():
    print("Starting")
    chat = Chat()
    ft.app(target=chat.ui)



if __name__ == "__main__":
    main()




