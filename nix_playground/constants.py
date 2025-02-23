# the playground metadata folder
PLAYGROUND_DIR = ".nix-playground"
# the filename of original checked out package name in the PLAYGROUND_DIR folder, like
# .nix-playground/pkg_name
PKG_NAME = "pkg_name"
# the filename of JSON dump from nix der file in the PLAYGROUND_DIR folder, like
# .nix-playground/drv.json
DRV_JSON_FILE = "drv.json"
# the filename of link to nix package in the PLAYGROUND_DIR folder, like
# .nix-playground/pkg
PKG_LINK = "pkg"
# the filename of link to nix source code in the PLAYGROUND_DIR folder, like
# .nix-playground/src
SRC_LINK = "src"
# the filename of link to nix build output in the PLAYGROUND_DIR folder, like
# .nix-playground/result
RESULT_LINK = "result"
# the filename of link to checked out folder in PLAYGROUND_DIR folder, like
# .nix-playground/checkout
CHECKOUT_LINK = "checkout"
# the filename of generated patch file in PLAYGROUND_DIR folder, like
# .nix-playground/checkout.patch
PATCH_FILE = "checkout.patch"
# the filename of package patch files folder in PLAYGROUND_DIR folder, like
# .nix-playground/pkg-patches
PKG_PATCHES_DIR = "pkg-patches"

CHECKOUT_GIT_AUTHOR_NAME = "nix-playground"
CHECKOUT_GIT_AUTHOR_EMAIL = "noreply@launchplatform.com"

# the default checkout folder name
DEFAULT_CHECKOUT_DIR = "checkout"
# the default flake to use if not provided
DEFAULT_FLAKE = "nixpkgs"
