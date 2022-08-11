from __future__ import annotations, print_function
import importlib
import shutil
import os
import io
from platform import system as what_platform
from enum import Enum
from typing import List, NoReturn

# TO-DO: Make the build script simpler!


"""
TARGET (str):
    Target script which is the "Entry Point"

BATCH_ONLY (boolean):
    Whether it should patch the target script to be only for
    batch decompiling, allowing to simply drop the unpacked
    DAT folder onto the EXE

ONE_FILE (boolean):
    If "True", a single executable will be generated

REQUIRE_ADMIN (boolean):
    Only effects Windows builds.
    It is recommended to keep this at "True" such that the app
    is not dealing with any potential privilege issues

ICON (str):
    Only applies if ICON field is NOT None.
    Sets an executable icon for Windows systems.
    ICON should either be None or a string path
    to a proper ".ico" file
"""
TARGET: str = "__init__.py"
BATCH_ONLY: bool = False
ONE_FILE: bool = True
REQUIRE_ADMIN: bool = True
ICON: str = None

# Helper...
def ASSERT_STR(inp: str) -> bool:
    assert type(inp) is str, "Must be type STRING (str)"
    return True

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
class DynImportError(Exception):
    def __init__(self, m):
        super().__init__(m)

"""
Automatically detects the platform
and selects the appropriate build tool accordingly.
Exits with [DynImportError] upon failure.
"""
def dyn_import_build_tool(plat: str) -> object or NoReturn:
    if (Platform.is_windows(plat) or Platform.is_linux(plat)):
        try:
            bt = importlib.import_module(".__main__","PyInstaller")
        except:
            raise DynImportError(
                "Make sure that you have PyInstaller, sillygoose!"
            )
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
    should_patch = None
    PATCHED_FN = None

    class RM_T(WEnum):pass

    def patch_target(self):pass
    def gen_opts(self):pass
    def start_build(self):pass
    def gen_opts(self):pass
    def finalize_build(self):pass
    def clean_up(self):pass

class WBuilder(Builder):
    PATCHED_FN = "patched.py"
    def __new__(cls):
        # dynamically choose which build tool depending on platform
        # currently just PyInstaller for Linux & Windows
        print("\nDetecting platform...")
        cls.current_platform = Platform.get_platform()
        print("You are on {}".format(cls.current_platform.upper()))
        cls.build_tool = dyn_import_build_tool(cls.current_platform)
        print("Build tool selected: {}\n\n".format(cls.build_tool.__name__))

        global TARGET
        assert type(TARGET) == str, "\'TARGET\' must be a STRING (str)"
        cls.target_script = TARGET

        global BATCH_ONLY
        assert type(BATCH_ONLY) == bool, "\'BATCH_ONLY\' must be a BOOLEAN (bool)"
        cls.should_patch = BATCH_ONLY

        return super().__new__(cls)


    def __init__(self):
        self.entry_script = self.target_script if not self.should_patch else self.PATCHED_FN
        self.opts = None
        self.isw:bool = Platform.is_windows(self.current_platform)
        self.isl: bool = Platform.is_linux(self.current_platform)

    def start_build(self):
        print("\nBuilding...")
        (
            self
                .patch_target()
                .gen_opts()
                .finalize_build()
                .clean_up()
        )

    def patch_target(self) -> object:
        if self.should_patch:
            print("\nPatching entry (BATCH_ONLY = True)...")
            t = io.open(self.target_script,"r")
            content = t.read()
            t.close()
            content = content.replace("\"--decompileAll\" in sys.argv","True")
            content = content.replace(".argv[1:]",".argv[0:]")
            p = io.open(self.entry_script,"w")
            p.write(content)
            p.close()
            print("Done Patching.\n\n")
        return self

    def gen_opts(self) -> object:
        print("Generating options...")
        global ONE_FILE, REQUIRE_ADMIN, ICON

        if (self.isw or
            self.isl):
            self.opts = []
            self.opts.append(self.entry_script)
            self.opts.append("-n=MrbDecompiler")
            self.opts.append("--clean")
            self.opts.append("-y")
            self.opts.append("--log-level=ERROR")
            assert type(ONE_FILE) == bool, "\'ONE_FILE\' must be BOOLEAN (bool)"
            if (ONE_FILE):
                self.opts.append("--onefile")
            if self.isw and (ICON != None) and (ASSERT_STR(ICON)):
                self.opts.append("-i={}".format(ICON))
            if self.isw and REQUIRE_ADMIN:
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
        rm_file(self.PATCHED_FN)

        return self

if __name__ == "__main__":
    b = WBuilder()
    b.start_build()
    print("\n\nDone. Build can be found in the \'dist\' folder")
