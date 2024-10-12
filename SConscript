import os
import subprocess
from SCons.Script import Environment, SConscript, Builder
from SCons.Script import  Dir, File, Export

PREFIX = "arm-none-eabi-"
BUILDER = "DEV"

common_flags = []

carlink_root = Dir('.')

if os.getenv("RELEASE"):
    BUILD_TYPE = "RELEASE"
    cert_fn = os.getenv("CERT")
    assert cert_fn is not None, 'No certificate file specified. Please set CERT env variable'
    assert os.path.exists(cert_fn), 'Certificate file not found. Please specify absolute path'
else:
    BUILD_TYPE = "DEBUG"
    cert_fn = File("./certs/debug").srcnode().relpath
    common_flags += ["-DALLOW_DEBUG"]

    if os.getenv("DEBUG"):
        common_flags += ["-DDEBUG"]

def objcopy(source, target, env, for_signature):
    return '$OBJCOPY -O binary %s %s' % (source[0], target[0])

def get_version(builder, build_type):
    try:
        git = subprocess.check_output(["git", "rev-parse", "--short=8", "HEAD"], encoding='utf8').strip()
    except subprocess.CalledProcessError:
        git = "unknown"
    return f"{builder}-{git}-{build_type}"

def get_key_header(name):
    from Crypto.PublicKey import RSA

    public_fn = File(f'./certs/{name}.pub').srcnode().get_path()
    with open(public_fn) as f:
        rsa = RSA.importKey(f.read())
    assert (rsa.size_in_bits() == 1024)

    rr = pow(2 ** 1024, 2, rsa.n)
    n0inv = 2 ** 32 - pow(rsa.n, -1, 2 ** 32)

    r = [
        f"RSAPublicKey {name}_rsa_key = {{",
        f"  .len = 0x20,",
        f"  .n0inv = {n0inv}U,",
        f"  .n = {to_c_uint32(rsa.n)},",
        f"  .rr = {to_c_uint32(rr)},",
        f"  .exponent = {rsa.e},",
        f"}};",
    ]
    return r

def to_c_uint32(x):
    nums = []
    for _ in range(0x20):
        nums.append(x % (2 ** 32))
        x //= (2 ** 32)
    return "{" + 'U,'.join(map(str, nums)) + "U}"

def build_project(project_name, project, extra_flags):
    linkerscript_fn = File(project["LINKER_SCRIPT"]).srcnode().relpath

    flags = project["PROJECT_FLAGS"] + extra_flags + common_flags + [
    "-Wall",
    "-Wextra",
    "-Wstrict-prototypes",
    "-Werror",
    "-mlittle-endian",
    "-mthumb",
    "-nostartfiles",
    "-fno-builtin",
    "-std=gnu11",
    "-fmax-errors=1",
    f"-T{linkerscript_fn}",
    "-lc",
    "-lm",
]

    includes = [
        '.',
        '..',
        carlink_root,
        f"{carlink_root}/base/",
    ]

    env = Environment(
        ENV=os.environ,
        CC=PREFIX + 'gcc',
        AS=PREFIX + 'gcc',
        OBJCOPY=PREFIX + 'objcopy',
        OBJDUMP=PREFIX + 'objdump',
        CFLAGS=flags,
        ASFLAGS=flags,
        LINKFLAGS=flags,
        CPPPATH=includes,
        ASCOM="$AS $ASFLAGS -o $TARGET -c $SOURCES",
        BUILDERS={
            'Objcopy': Builder(generator=objcopy, suffix='.bin', src_suffix='.elf')
        },
        tools=["default", "compilation_db"],
    )

    startup = env.Object(f"obj/startup_{project_name}", project["STARTUP_FILE"])

    # Bootstub
    crypto_obj = [
        env.Object(f"rsa-{project_name}", f"{carlink_root}/crypto/rsa.c"),
        env.Object(f"sha-{project_name}", f"{carlink_root}/crypto/sha.c")
    ]
    bootstub_obj = env.Object(f"bootstub-{project_name}", File(project.get("BOOTSTUB", f"{carlink_root}/base/bootstub.c")))
    bootstub_elf = env.Program(f"obj/bootstub.{project_name}.elf",
                               [startup] + crypto_obj + [bootstub_obj])
    env.Objcopy(f"obj/bootstub.{project_name}.bin", bootstub_elf)

    # build main
    main_obj = env.Object(f"main-{project_name}", project["MAIN"])
    main_elf = env.Program(f"obj/{project_name}.elf", [startup, main_obj],
                           LINKFLAGS=[f"-Wl,--section-start,.isr_vector={project['APP_START_ADDRESS']}"] + flags)
    main_bin = env.Objcopy(f"obj/{project_name}.bin", main_elf)

    # sign main
    sign_py = File(f"{carlink_root}/crypto/sign.py").srcnode().relpath
    env.Command(f"obj/{project_name}.bin.signed", main_bin, f"SETLEN=1 {sign_py} $SOURCE $TARGET {cert_fn}")

base_project_f4 = {
    "MAIN": "main.c",
    "STARTUP_FILE": File("./base/stm32f4/startup_stm32f413xx.s"),
    "LINKER_SCRIPT": File("./base/stm32f4/stm32f4_flash.ld"),
    "APP_START_ADDRESS": "0x8004000",
    "PROJECT_FLAGS": [
        "-mcpu=cortex-m4",
        "-mhard-float",
        "-DSTM32F4",
        "-DSTM32F413xx",
        "-Ibase/stm32f4/inc",
        "-mfpu=fpv4-sp-d16",
        "-fsingle-precision-constant",
        "-Os",
        "-g",
    ],
}

Export('base_project_f4', 'build_project')

# comm autogenerated includes
with open("base/obj/gitversion.h", "w") as f:
    f.write(f'const uint8_t gitversion[] = "{get_version(BUILDER, BUILD_TYPE)}";\n')

with open("base/obj/version", "w") as f:
    f.write(f'{get_version(BUILDER, BUILD_TYPE)}')

certs = [get_key_header(n) for n in ["debug", "release"]]
with open("base/obj/cert.h", "w") as f:
    for cert in certs:
        f.write("\n".join(cert) + "\n")

# carlink firmware
SConscript('base/SConscript')
