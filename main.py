import json
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
if not (
    commands_file := os.path.join(os.curdir, "res/commands.json")
) and not os.path.isfile(commands_file):
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

        # Check length of command
        if len(command) < 1 or not command.startswith("/"):
            return "Comando no reconocido. Prueba a usarlo con \"/\""

        command = command.removeprefix("/")
        cmd, *params = command.split(" ") # command_name [param1, param2, ...]

        if not hasattr(COMMANDS, cmd):
            print("Comando no reconocido. Usa /help para listar los comandos disponibles")
            return self.help()
        method_name = getattr(self, cmd)

        try:
            if method_name == "exit":
                EXIT = True
                return ""

            # Check args
            expected_params = sum(1 for p in getattr(COMMANDS, cmd) if not p.startswith("_"))
            if len(params) > expected_params:
                print("Too many args. Expected:\n")
                return self.help(cmd)
            if not params and expected_params:
                print("Missing args:\n")
                return self.help(cmd)

            return method_name(*params)
        except Exception as e:
            return f"Error al ejecutar el comando {cmd}: {e}"


    def _process_params(self, params: dict) -> str:
        """
        param 	:   description | required
        param2 	:   description | optional
        param3 	:   description | required
            structure   :   [-1, -1, -1]

        Parameters
        ----------
        params : dict
            _description_
        """
        interface = "Parameters\n----------\n"
        for key, value in params.items():
            interface += (
                f"{key}   :   {value['_description']} | "
                f"{'required' if value['required'] > 0 else 'optional'}"
                f"\n"
            )

            if structure := value.get("structure"):
                interface += f"\n\tstructure    :   {structure}\n"

        return interface


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

    def help(self, command_name: Union[str, list] = "") -> str:
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
        interface = ""
        command_names = (
            [command_name] 
            if isinstance(command_name, str)
            else [cmd for cmd in dir(COMMANDS) if not cmd.startswith("_")]
        )

        try:
            for command in command_names:
                command_attrs = getattr(COMMANDS, command, None)
                if not command_attrs:
                    return f"No se ha encontrado ayuda para el comando {command}"
                interface += str(command)

                # Alias + Description
                if (alias := command_attrs.get("_alias")):
                    interface += f" | {alias}\n"
                interface += f"     {command_attrs.get('_description')}\n\n"

                # Params
                if params := {k: v for k, v in command_attrs.items() if isinstance(v, dict)}:
                    interface += self._process_params(params)
                interface += "\n\n"
        except Exception as e:
            command_name = (
                command_name[0] if isinstance(command_name, list) else command_name
            )
            return (
                "Error al obtener información acerca de"
                f"{'l comando ' + command_name if command_name else ' los comandos'}: {e}"
            )

        return interface
#endregion


def main():
    global EXIT
    app = LostCrop()

    while not EXIT:
        command = input("> ")
        print(app._proccess_commands(command=command))


if __name__ == "__main__":
    main()