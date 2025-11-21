import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import gspread
from google.oauth2.service_account import Credentials
from mcstatus import BedrockServer, JavaServer

# region Config
# Minecraft
MC_VERSIONS = {1: JavaServer, 2: BedrockServer}
WORLD_PAGES = {0: "overworld", 1: "nether", 2: "end"}

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
EXIT = False

# Google
SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
if not SERVICE_ACCOUNT_FILE or not os.path.isfile(SERVICE_ACCOUNT_FILE):
    print("No existen las credenciales de acceso")
    # sys.exit()

# Lang
LANG = "es"

# Commands
if not (
    commands_file := os.path.join(
        Path(__file__).resolve().parent, f"res/commands_{LANG}.json"
    )
) or not os.path.isfile(commands_file):
    print("Error al obtener los comandos.")
    sys.exit()

try:
    commands = {}
    with open(commands_file, encoding="utf-8") as f:
        try:
            commands = json.load(f)
        except Exception:
            pass
        finally:
            f.close()
    COMMANDS = SimpleNamespace(**commands)
except Exception as e:
    print(f"Error al obtener los comandos: {e}")
    sys.exit()
# endregion


def proccess_commands(command: str) -> str:
    global EXIT

    # Check length of command
    if len(command) < 1 or not command.startswith("/"):
        return 'Comando no reconocido. Prueba a usarlo con "/"'

    command = command.removeprefix("/")
    cmd, *params = command.split(" ")  # command_name [param1, param2, ...]

    if cmd == "exit":
        EXIT = True
        return ""

    # Command has args (e.g. --help)
    try:
        arguments = [arg for arg in params if arg.startswith("--")]
        if arguments:
            """
            Lo más sencillo sería pasar a: return method_name(*params)
            lo siguiente -> return method_name(*args, *params)
            y dentro de cada metodo validar los args

            DE MOMENTO SOLO HELP TIENE ARGS
            """
            pass
    except Exception as e:
        return f"Error al obetner los argumentos del comando {cmd}: {e}"

    try:
        method_name = globals().get(cmd)
        if not method_name:
            print(
                "Comando no reconocido. Usa /help para listar los comandos disponibles"
            )
            return help()

        # Check args
        expected_params = sum(
            1 for p in getattr(COMMANDS, cmd) if not p.startswith("_")
        )

        if len(params) > expected_params:
            print("Too many args. Expected:\n")
            return help(cmd)
        if not params and expected_params:
            print("Missing args:" if method_name != help else "List of commands:")
            return help(cmd)

        return method_name(*params)
    except Exception as e:
        return f"Error al ejecutar el comando {cmd}: {e}"


def process_params(params: dict, extra_tab: bool = False) -> str:
    """Return the params of the command in a beautiful way.

    Parameters
    ----------
    params : dict
        Params to process
    extra_tab : bool
        Whether to add an extra tab for formatting

    Returns
    -------
    str
        Beautified params

    """
    interface = ""
    for key, value in params.items():
        if key == "arguments":
            interface += "\tOptions:"
            for k, v in value.items():
                interface += (
                    f"\n\t    {process_params({k: v}, extra_tab=True)}"
                )
            interface += "\n"
            continue
        interface += (
            f"\t[{key}] ({'required' if value['required'] > 0 else 'optional'})"
            # If extra_tab is present, we are processing arguments (e.g. --lang)
            + ("\n\n\t    " if extra_tab else "\n\n")
            + "\tAbout:\n"
            + ("\t    " if extra_tab else "")
            + f"\t{value['_description']}\n\n"
        )

        if structure := value.get("structure") or value.get("possible_values"):
            title = "Available values" if value.get("possible_values") else "Structure"
            interface += (
                # If extra_tab is present, we are processing arguments (e.g. --lang)
                ("\n\t    " if extra_tab else "\n")
                + f"\t{title}:\n"
                + ("\t    " if extra_tab else "")
                + f"\t{structure}\n\n"
            )

    return interface


def process_arguments(args: list[str]) -> dict:
    return {}


def _get_spreadsheet(
    spreadsheet_name: str, page_no: int
) -> gspread.worksheet.Worksheet | None:
    """Obtener la hoja de coordenadas de Google Spreadsheets.

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
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        client = gspread.authorize(creds)

        return client.open(spreadsheet_name).get_worksheet(page_no)
    except Exception as e:
        print(f"Fallo al intentar obtener el archivo: {e}")
        return


def _get_mc_version(version: int) -> type[JavaServer] | type[BedrockServer] | None:
    """Obtener la clase `mcstatus.JavaServer` o `mcstatus.BedrockServer`.

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


# region Commands
def check_server_status(server_name: str, m_version: int = 1) -> str:
    """Comprobar si el servidor está activo.

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
        server = _get_mc_version(m_version)
        if not server:
            return "Ingresa una versión de Minecraft válida"

        status = server.lookup(server_name).status()
        return f"Status {status} - Ping: {status.latency}ms"
    except Exception as e:
        return f"Servidor offline o inaccesible: {e}"


def check_cur_players(server_name: str, m_version: int = 1) -> str:
    """Obtener la cantidad de jugadores.

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
        server = _get_mc_version(m_version)
        if not server:
            return "Ingresa una versión de Minecraft válida"

        status = server.lookup(server_name).status()
        print(f"Jugadores online: {status.players.online}")

        if not (po := status.players.online):
            return "No se pudieron obtener los nombres (Aternos puede bloquearlo)."
        return f"Jugadores conectados: {po}"
    except Exception as e:
        return f"Error al consultar jugadores: {e}"


def save_coords(coords: list[str], page_no: int = 1) -> str:
    return "OK"

    try:
        sheet = _get_spreadsheet(spreadsheet_name="", page_no=page_no)
        if not sheet:
            return "No se ha encontrado la página en la que insertar"

        sheet.append_row(coords)
        return f"Coordenadas guardadas: {coords} en {WORLD_PAGES.get(page_no)}"
    except Exception as e:
        return f"Error guardando coordenadas: {e}"


def help(command_name: str | list = "") -> str:
    """Show information about one or all the commands.

    Parameters
    ----------
    command_name : str, optional
        Comando del que obtener información. Si no se indica,
        se devuelven todos los comandos disponibles

    Returns
    -------
    str
        Interfaz informativa o error en su defecto

    """
    interface = ""
    command_names = (
        [command_name]
        if isinstance(command_name, str) and command_name != "help"
        else [cmd for cmd in dir(COMMANDS) if not cmd.startswith("_")]
    )

    try:
        for command in command_names:
            command_attrs = getattr(COMMANDS, command, None)
            if not command_attrs:
                return f"No se ha encontrado ayuda para el comando {command}"
            interface += f"\n\nUsage: {command}"

            # Alias + Description
            if alias := command_attrs.get("_alias"):
                interface += f"\n\n    Alias:\n    {alias}"
            interface += f"\n\n    About:\n    {command_attrs.get('_description')}"

            # Params
            if params := {
                k: v for k, v in command_attrs.items() if isinstance(v, dict)
            }:
                interface += f"\n\n    Arguments:\n    {process_params(params)}"
    except Exception as e:
        command_name = (
            command_name[0] if isinstance(command_name, list) else command_name
        )
        return (
            "Error al obtener información acerca de"
            f"{'l comando ' + command_name if command_name else ' los comandos'}: {e}"
        )

    return interface


# endregion


def init_console():
    """Initialize commands."""
    while not EXIT:
        command = input("> ")
        print(proccess_commands(command=command))
