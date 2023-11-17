from time import sleep
from random import random
from threading import Thread
from queue import Queue
from queue import Empty
import flet as ft
import serial.tools.list_ports
import serial
import datetime
from faker import Faker




class SerialController:

    serialPort = "COM3"
    baudRate = 115200
    address = "AB"
    running = False
    ser = None


    def __init__(self) -> None:
        self.send_queue = Queue()
        self.receive_queue = Queue()

    
    def get_ports(self) -> list:
        ports = serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(ports):
            print("{}: {} [{}]".format(port, desc, hwid))
        return [p.device for p in ports]

    def _setup_device(self) -> None:
        self.ser.write(str.encode(f"a[{self.address}]\n"))
        sleep(0.1)
        self.ser.write(str.encode("c[1,0,5]\n"))
        sleep(0.1)
        self.ser.write(str.encode(f"c[0,1,30]\n"))
        sleep(0.1)



    def start(self, serialPort: str, baudRate: int, address: str) -> None:
        self.serialPort = serialPort
        self.baudRate = baudRate
        self.address = address
        self.running = True

        self.ser = serial.Serial(port=self.serialPort, baudrate=self.baudRate, timeout=0.1)

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
        self.ser.write(f"m[{data},FF]\n".encode())

    def _receive_from_serial(self) -> str:
        # randomly return a message 
        # if random() < 0.05:
        #     return "Peter:Hello"
        # else:
        #     return ""
        data = self.ser.readline().decode()
        if(data != ""):
            print(f"Received {data}")
        return data
    


    def _run(self) -> None:
        sleep(2)
        self._setup_device()
        while self.running:
            try:
                data = self.send_queue.get(timeout=0.1)
            except Empty:
                pass
            else:
                self._send_send_to_serial(data)
            try:
                data = self._receive_from_serial()
            except Empty:
                pass
            else:
                if(data != ""):
                    self.receive_queue.put(data)
            sleep(0.01)



class Message:
    message = ""
    time = ""
    srcName = ""
    sentBySelf = False
    sentBySystem = False

    def __init__(self, message: str, srcName: str, sentBySelf: bool = False, sentBySystem: bool = False) -> None:
        self.message = message
        self.srcName = srcName
        self.time = datetime.datetime.now().strftime("%H:%M")
        self.sentBySelf = sentBySelf
        self.sentBySystem = sentBySystem
    
class Chat:
    ftPage = None
    displaySetup = True
    serialCtl = None
    name = ""
    address = ""
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

        
    def _get_msg_self_sent(self, message : Message) -> ft.Row:
        row = ft.Row([ft.Text(message.message, color=ft.colors.BLACK87),ft.Text(f": {self.name}", color=ft.colors.BLACK87), ft.Text(message.time)], spacing=10, alignment=ft.MainAxisAlignment.END)

        container = ft.Container(content=row, padding=10, border_radius=5, bgcolor=ft.colors.ORANGE_400, shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=0,
            color=ft.colors.BLUE_GREY_300,
            offset=ft.Offset(0, 0),
            blur_style=ft.ShadowBlurStyle.OUTER,
        ))

        return container 
    
    def _get_msg_other_sent(self, message : Message) -> ft.Row:
        
        row = ft.Row([ft.Text(message.time), ft.Text(f"{message.srcName}:", color=ft.colors.BLACK87), ft.Text(message.message,  color=ft.colors.BLACK87) ], spacing=10)
        container = ft.Container(content=row, padding=10, border_radius=5, bgcolor=ft.colors.BLUE_200, shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=0,
            color=ft.colors.BLUE_GREY_300,
            offset=ft.Offset(0, 0),
            blur_style=ft.ShadowBlurStyle.OUTER,
        ))

        return container


    def get_message_element(self, message : Message) -> ft.Row:
        if(message.sentBySelf):
            return self._get_msg_self_sent(message)
        elif (message.sentBySystem):
            return self._get_msg_system(message)
        else:
            return self._get_msg_other_sent(message)

    def add_message(self, message : Message) -> None:
        self.massagesView.controls.append(self.get_message_element(message))
        self.ftPage.update()

    def _run_receive(self) -> None:
        while True:
            message = self.serialCtl.receive()
            if(message != ""):

                split = message.split(":")

                if(len(split) < 2):
                    self.ftPage.pubsub.send_all(Message(message.rstrip(), "sys", sentBySelf=False, sentBySystem=True))
                
                else:
                    name = split[0]
                    text = ":".join(message.split(":")[1:])
                    self.ftPage.pubsub.send_all(Message(text.rstrip(), name, sentBySelf=False))
            sleep(0.1)

    def _get_setup_view(self) -> ft.View:
        portList = [ft.dropdown.Option(p) for p in self.serialCtl.get_ports()]

        if(len(portList) == 0):
            self.show_no_port_banner()
            portList = [ft.dropdown.Option("No Ports Found")]
        else:
            self.close_banner(None)

        portDD = ft.Dropdown( width=300,options=portList, value=portList[0])
        addressTF = ft.TextField(hint_text="AA", width=300)
        nameTF = ft.TextField(hint_text="", width=300)
        
        return ft.View(
            "/",
            [
                ft.Text("Select Port"),
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
        self.serialCtl.send(f"{self.name}:{message}")
        self.ftPage.pubsub.send_all(Message(message, self.name, sentBySelf=True))
        
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
        page.title = "VLC Chat"
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

    def submitSetup(self, address : str, port : str, name: str ) -> None:
        if(len(name) == 0):
            name = "Anonymous"
        
        if(address == "" or int(address, 16) <= 0 or int(address, 16) > 254):
            self.show_invalid_address_banner()
            return
        

        if(port == "" or port is None or port == "No Ports Found"):
            self.show_invalid_port_banner()
            return


        self.displaySetup = False
        self.name = name
        self.address = address
        self.port = port
        self.serialCtl.start(port, 9600, address)
        self.ftPage.go("/no_route")

        self.recThread = Thread(target=self._run_receive)
        self.recThread.start()




def main():
    print("Starting")
    chat = Chat()
    ft.app(target=chat.ui)



if __name__ == "__main__":
    main()




