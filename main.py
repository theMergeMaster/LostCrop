import inspect
import json
import logging
import os
from types import SimpleNamespace
from typing import Type, Union

import gspread
from google.oauth2.service_account import Credentials
from mcstatus import BedrockServer, JavaServer


# MC config
MC_VERSIONS = {1: JavaServer, 2: BedrockServer}
WORLD_PAGES = {0: "overworld", 1: "nether", 2: "end"}

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
EXIT = False

# Initialize commands
if not (commands_file := os.path.join(os.curdir, 'res/commands.json')) and os.path.isfile(commands_file):
    print("Error al obtener los comandos.")
    exit()

commands = {}
with open(commands_file, 'r', encoding='utf-8') as f:
    try:
        commands = json.load(f)
    except Exception:
        pass
    finally:
        f.close()
COMMANDS = SimpleNamespace(**commands)


class LostCrop:
    def __init__(self):
        """
        Obtener cierta información de algún servidor de Minecraft (ya sea Java o Bedrock)
        """

        self.service_account_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")

        if not self.service_account_file or not os.path.isfile(self.service_account_file):
            print("No existen las credenciales de acceso")
            return


    def _proccess_commands(self, command: str) -> str:
        global EXIT
        if not command.startswith("/"):
            return "Comando no reconocido. Prueba a usarlo con \"/\""

        command = command.removeprefix("/")
        command_partition = command.split(" ")
        
        if not hasattr(COMMANDS, command_partition[0]):
            print("Comando no reconocido. Usa /help para listar los comandos disponibles")
            return self.help()
        cmd = getattr(LostCrop, command_partition[0])

        try:
            if cmd == "exit":
                EXIT = True
                return ""
            cmd_args_names = [p for p in getattr(COMMANDS, command_partition[0]) if not p.startswith("_")]

            if len(command_partition[1:]) > len(cmd_args_names):
                return "Demasiados argumentos"
            if not command_partition[1:] and len(cmd_args_names):
                return "Faltan args" #TODO Devolver self.help(command_partition[0])
            
            return cmd(command_partition[1:])
        except Exception as e:
            return f"Error al ejecutar el comando {cmd}: {e}"


    def _process_params(self, params: dict):
        pass


    def _get_spreadsheet(self, spreadsheet_name: str, page_no: int) -> gspread.worksheet.Worksheet | None:
        """
        Obtener la hoja de coordenadas de Google Spreadsheets

        Parameters
        ----------
        spreadsheet_name : str
            Nombre del Spreadsheets
        page_no : int
            Página en la que se van a guardar las coordenadas. Siendo:
        ```
            {"overworld": 0, "nether": 1, "end": 2}
        ```

        Returns
        -------
        gspread.worksheet.Worksheet | None
            Hoja (si la encuentra) que queremos consultar
        """
        try:
            creds = Credentials.from_service_account_file(self.service_account_file, scopes=SCOPES)
            client = gspread.authorize(creds)

            return client.open(spreadsheet_name).get_worksheet(page_no)
        except Exception as e:
            print(f"Fallo al intentar obtener el archivo: {e}")
            return


    def _get_mc_version(self, version: int) -> Union[Type[JavaServer], Type[BedrockServer]] | None:
        """
        Obtener la clase `mcstatus.JavaServer` o `mcstatus.BedrockServer` dependiendo de lo que queramos

        Parameters
        ----------
        version : int
            Versión que queremos, siendo:
        ```
            {1: JavaServer, 2: BedrockServer}
        ```

        Returns
        -------
        Union[Type[JavaServer], Type[BedrockServer]] | None
            Objeto de clase servidor
        """
        try:
            mc_version = MC_VERSIONS.get(version)
            if not mc_version:
                print("Ingresa una versión de Minecraft válida")

            return mc_version
        except Exception as e:
            print(f"Ha habido un fallo al obtener la versión indicada: {e}")
            return


#region Commands
    def check_server_status(self, server_name: str, m_version: int = 1) -> str:
        """
        Comprobar si el servidor está activo

        Parameters
        ----------
        server_name : str
            Nombre del servidor
        m_version : int
            Versión de Minecraft. Puede ser `Java` o `Bedrock`. Default 1 (`Java`)
        """

        input(f"{server_name = }\n{m_version = }")
        return "OK"

        try:
            server = self._get_mc_version(m_version)
            if not server:
                return "Ingresa una versión de Minecraft válida"

            status = server.lookup(server_name).status()
            return f"Status {status} - Ping: {status.latency}ms"
        except Exception as e:
            return f"Servidor offline o inaccesible: {e}"


    def check_cur_players(self, server_name: str, m_version: int = 1) -> str:
        """
        Obtener la cantidad de jugadores.

        Parameters
        ----------
        server_name : str
            Nombre del servidor
        m_version : int
            Versión de Minecraft. Puede ser `Java` o `Bedrock`. Default 1 (`Java`)
        """

        input(f"{server_name = }\n{m_version = }")
        return "OK"
    
        try:
            server = self._get_mc_version(m_version)
            if not server:
                return "Ingresa una versión de Minecraft válida"

            status = server.lookup(server_name).status()
            print(f"Jugadores online: {status.players.online}")

            if not (po := status.players.online):
                return "No se pudieron obtener los nombres (Aternos puede bloquearlo)."
            return f"Jugadores conectados: {po}"
        except Exception as e:
            return f"Error al consultar jugadores: {e}"


    def save_coords(self, coords: list[str], page_no: int = 1) -> str:
        input(f"{coords = }\n{page_no = }")
        return "OK"
    
        try:
            sheet = self._get_spreadsheet(spreadsheet_name="", page_no=page_no)
            if not sheet:
                return "No se ha encontrado la página en la que insertar"

            sheet.append_row(coords)
            return f"Coordenadas guardadas: {coords} en {WORLD_PAGES.get(page_no)}"
        except Exception as e:
            return f"Error guardando coordenadas: {e}"


    def help(self, command_name: str = "") -> str:
        """
        Mostrar información de un comando o de todos

        ```
        command_name | alias : description

        param 	:   description | required
        param2 	:   description | optional
        param3 	:   description | required
            structure   :   [-1, -1, -1]
        ```

        Parameters
        ----------
        command_name : str, optional
            Comando del que obtener información. Si no se indica, se devuelven todos los comandos disponibles

        Returns
        -------
        str
            Interfaz informativa o error en su defecto
        """

        input(f"{command_name = }")
        return "OK"
    
        interface = ""
        command_names = (
            [getattr(COMMANDS, command_name)]
            if command_name
            else inspect.getmembers(COMMANDS)
        )

        try:
            for command in command_names:
                interface += command

                # Alias + Description
                if (alias := getattr(command, "_alias")):
                    interface += f" | {alias}"
                interface += f" : {getattr(command, '_description')}\n\n"

                # Params
                if (params := [
                    p for p in inspect.getmembers(command) if not p[0].startswith("_")
                ]):
                    interface += self._process_params(params)
        except Exception as e:
            return (
                f"Error al obtener información acerca de "
                f"{'el comando ' + command_name if command_name else 'los comandos'}: {e}"
            )

        return interface
#endregion


def main():
    global EXIT
    app = LostCrop()

    print("=== LostCrop CLI ===")

    while not EXIT:
        command = input("> ")
        print(app._proccess_commands(command=command))

    print("Final de programa")


if __name__ == "__main__":
    main()