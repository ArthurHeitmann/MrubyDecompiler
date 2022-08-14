from __future__ import annotations, print_function
import importlib
import shutil
import os
from platform import system as what_platform
from enum import Enum
from typing import List, NoReturn


"""
TARGET (str):
    Target script which is the "Entry Point"

ONE_FILE (boolean):
    If "True", a single executable will be generated

REQUIRE_ADMIN (boolean):
    Only effects Windows builds.
    Only set this to "True" if you experience
    application privilege issues on Windows.

ICON (str):
    Only applies if ICON field is NOT None.
    Sets an executable icon for Windows systems.
    ICON should either be None or a string path
    to a proper ".ico" file
"""

# IMPORTANT TIP! (VERY SECRET)

# If you run this script ("build_release.py")
# with the option -OO, it will build it in "RELEASE MODE"
# This will remove any assert, __debug__ dependent statements,
# and docstrings from the decompiler.
# This results in a smaller binary (executable), and hopefully
# a bit faster :)
# Unfortunately at the cost of your release being harder to debug.
# But you can always just download the source of the release,
# and run the build script without -OO to have an executable
# fitting for finding out what's wrong when replicating the user's bug.

# So run it like this... with (INTERPRETER) being whatever your Python binary is
#   (INTERPRETR) -OO build_release.py

TARGET: str = "__init__.py"
ONE_FILE: bool = True
REQUIRE_ADMIN: bool = False
ICON: str = None

def WASSERT(t: type, x) -> bool:
    assert type(x) is t, "Must be type {}".format(t.__name__)
    return True

# wrap WASSERT...
def ASSERT_STR(inp: str) -> bool:
    return WASSERT(str, inp)

def ASSERT_BOOL(inp: bool) -> bool:
    return WASSERT(bool, inp)

def ASSERT_INT(inp: int) -> bool:
    return WASSERT(int, inp)

"""
Enum Wrapper
"""
class WEnum(Enum):
    @classmethod
    def get(cls, attr:str) -> object:
        return cls.__dict__[attr].value

"""
Recognized Platforms
"""
class Platforms(WEnum):
    win: str = "windows"
    lnx: str = "linux"
    osx: str = "darwin"

"""
Kinda Redundant Not Gonna Lie
"""
class Platform(object):
    __supported_platforms = [
        Platforms.get("win"),
        Platforms.get("lnx")
    ]

    @staticmethod
    def get_platform() -> str:
        return what_platform().lower()

    @staticmethod
    def is_windows(plat: str) -> bool:
        return plat == Platforms.get("win")

    @staticmethod
    def is_linux(plat: str) -> bool:
        return plat == Platforms.get("lnx")

    @classmethod
    def supported_platforms(cls) -> List[str]:
        return cls.__supported_platforms

"""
Exception to be thrown by
[dyn_import_build_tool] if not on a supported platform
"""
class DynImportError(BaseException):
    def __init__(self, m):
        super().__init__(m)

"""
Wrapper for importlib.import_module
"""
def try_import(part: str, main_module: str) -> object or NoReturn:
    # In Python versions 3.6 and above, importlib.import_module
    # will throw a ModuelNotFoundError (only available in 3.6 and above)
    # But, ModuleNotFoundError inherits from ImportError, so we can
    # just use that instead for compatibility...
    def concat_imp_mod() -> str:
        # so i can take advantage of "nonlocal" for once
        # lol, must be one of the most unused Python features i swear

        #... although this could've been achieved as well with
        # functools.partial probably
        nonlocal part
        nonlocal main_module
        return main_module+part

    #def dyn_error() -> type:
    #    v = sys.version_info
    #    inheritable = None
    #    if (v.major >= 3 and v.minor >= 6):
    #        return ModuleNotFoundError
    #    return ImportError

    try:
        imp = importlib.import_module(part,main_module)
        return imp
    except ImportError: #dyn_error():
        raise DynImportError(
            "Make sure that you have {} installed, sillygoose!".format(
                concat_imp_mod()
            )
        )
    except:
        raise DynImportError(
            "An unknown error occurred whilst trying to import {}".format(
                concat_imp_mod()
            )
        )

"""
Selects the appropriate build tool,
in accordance with the currently selected platform.
Exits with [DynImportError] upon failure.
"""
def dyn_import_build_tool(plat: str) -> object or NoReturn:
    if (Platform.is_windows(plat) or Platform.is_linux(plat)):
        bt = try_import(".__main__","PyInstaller")
        return bt
    else:
        def gen_supported() -> str:
            supported: List[str] = Platform.supported_platforms()
            sup: str = ""
            for p in supported:
                sup += "\t\t"+p+"\n"

            return sup

        raise DynImportError(
            "\n\tNot on a supported platform.\n\tSupported platforms are:\n {}".format(
                str(gen_supported())
            )
        )

"""
Prototype for WBuilder...
(Also Redundant)
"""
class Builder(object):
    build_tool = None
    current_platform = None
    target_script = None

    class RM_T(WEnum):pass

    def gen_opts(self):pass
    def start_build(self):pass
    def gen_opts(self):pass
    def finalize_build(self):pass
    def clean_up(self):pass

class WBuilder(Builder):
    def __new__(cls):
        # dynamically choose which build tool depending on platform
        # currently just PyInstaller for Linux & Windows
        print("\nDetecting platform...")
        cls.current_platform = Platform.get_platform()
        print("You are on {}".format(cls.current_platform.upper()))
        cls.build_tool = dyn_import_build_tool(cls.current_platform)
        print("Build tool selected: {}\n".format(cls.build_tool.__name__))

        global TARGET
        ASSERT_STR(TARGET)
        cls.target_script = TARGET

        return super().__new__(cls)


    def __init__(self):
        self.OUTPUT_NAME = "MrbDecompiler"

        self.entry_script = self.target_script
        self.opts = None
        self.isw:bool = Platform.is_windows(self.current_platform)
        self.isl: bool = Platform.is_linux(self.current_platform)

    def start_build(self):
        print("\nBuilding...")
        (
            self
                .gen_opts()
                .finalize_build()
                .clean_up()
        )

    def gen_opts(self) -> object:
        print("Generating options...")
        global ONE_FILE, REQUIRE_ADMIN, ICON
        ASSERT_BOOL(ONE_FILE)
        ASSERT_BOOL(REQUIRE_ADMIN)
        # cant assert ICON since it can be None...

        if (self.isw or
            self.isl):
            self.opts = []
            self.opts.append(self.entry_script)
            self.opts.append("-n={}".format(self.OUTPUT_NAME))
            self.opts.append("--clean")
            self.opts.append("-y")
            self.opts.append("--log-level=ERROR")
            if (ONE_FILE):
                self.opts.append("--onefile")
            if self.isw:
                if (ICON != None) and (ASSERT_STR(ICON)):
                    self.opts.append("-i={}".format(ICON))
                if REQUIRE_ADMIN:
                    self.opts.append("--uac-admin")

        return self

    def finalize_build(self) -> object:
        print("Finalizing Build...")
        #print(self.build_tool)
        #print(self.opts)
        if self.isw or self.isl:
            self.build_tool.run(self.opts)
        #print(self.build_tool)
        return self

    """
    Enumeration for type when using
    [does_not_exist]
    """
    class RM_T(WEnum):
        FILE = 0
        DIRECTORY = 1

    def clean_up(self) -> object:
        print("Cleaning up...")

        def does_not_exist(n: str, t: str):
            tmpl = ["file","directory"]
            # no need to assert because it's checked in the wrappers already...
            print("\'{}\' {} does not exist, pushing forward..."
                .format(
                    n,tmpl[self.RM_T.get(t)]
                ))


        def rm_dir(dP: str) -> None:
            ASSERT_STR(dP)
            try:
                shutil.rmtree(dP)
            except:
                does_not_exist(dP,
                              "DIRECTORY")

        def rm_file(fP: str) -> None:
            ASSERT_STR(fP)
            try:
                os.remove(fP)
            except:
                does_not_exist(fP,
                                "FILE")

        rm_dir("build")
        rm_dir("__pycache__")
        rm_file(self.OUTPUT_NAME+".spec")

        return self

if __name__ == "__main__":
    b = WBuilder()
    b.start_build()
    print("\n\nDone. Build can be found in the \'dist\' folder")
