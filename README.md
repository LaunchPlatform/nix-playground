# nix-playground

The nix-playground is a command line tool that makes applying patches to the nixpkgs packages much easier.

## Example

```bash
# checkout libnvidia-container package source code locally
np checkout nixpkgs#libnvidia-container

# modify the code
vim checkout/src/cli/main.c

# build the package with changes you made in the checkout folder and try it out
np build

# output the patch for applying on the production environments
np patch > bugfix.patch

# clean up the generated files
np clean
```

## Why
Too often, we are afraid of digging into the upstream code, modifying and patching it because it's a very tedious process.
Just getting the project to build could take hours.
Thanks to [nixpkgs](https://nixos.org), building open-source software is much easier with a single source tree capable of building from the Linux kernel all the way to a simple utils command-line tool.
With nix-playground, now you can easily check out source code from a package, modify it, test it out, and then create patches effortlessly.

## Usage

This tool assumes you have [nixpkgs](https://nixos.org) with [flake](https://wiki.nixos.org/wiki/Flakes) and [Python](https://www.python.org) >= 3.11 installed on your environment.
To install nix-playground, simply run:

```bash
pip install nix-playground
```

Then, you can use the command line tool `np` (stands for nix-playground).
For example, say you need to apply a patch to [libnvidia-container](https://github.com/NVIDIA/libnvidia-container), with the `np` command, you can run:

```bash
np checkout nixpkgs#libnvidia-container
```

It will check the source code of `libnvidia-container` in the `checkout` folder of the current directory.
Next, you can modify the code in the `checkout` folder. The tool will track changes you made automatically.
Once you're done with the changes and would like to try it out, simply do the following:

```bash
np build
```

It will build the `libnvidia-container` package with patches from the changes you just made in the `checkout` folder.
The result will end up in the `result` folder, just like the `nix-build` command.
You can test the build. When you're happy with the result and decide to port the patch file to your production environments, you can run the command:

```bash
np patch > bugfix.patch
```

To print the patch file contents.
With the patch file, you can then apply it on the target package like this:

```nix
with import <nixpkgs> {};
    libnvidia-container.overrideAttrs (oldAttrs: {
        patches = (lib.attrsets.attrByPath ["patches"] [] oldAttrs) ++ [./bugfix.patch];
    })
```

### Checkout specific version

One of the issues we encountered while using nix-playground was the version we patched locally is different from the one running on our production environment.
To solve the problem, you can checkout specific version of nixpkgs or flake with the [flake reference URL schema](https://nix.dev/manual/nix/2.24/command-ref/new-cli/nix3-flake#examples).
For example, to fix a bug of `libnvidia-container` in the `nixpkgs` repo at commit `11415c7ae8539d6292f2928317ee7a8410b28bb9`, you can run the following

```bash
np checkout github:NixOS/nixpkgs/11415c7ae8539d6292f2928317ee7a8410b28bb9#libnvidia-container
```

## How it works

### Checkout

1. Create `.nix-playground` folder in the current directory
2. Call `nix derivation show` to output the derivation as a json file at `.nix-playground/drv.json`
3. Get the `env.src` nix store path from the generated derivation 
4. Run `nix-store --realise` to realise the package and its source derivation with links in the `.nix-playground` folder.
5. Deep copy the source (from env.src) folder, or untar it to the current directory's `checkout` folder
6. Init a git repo in the `checkout` folder and commit all the changes
7. Apply patches from the package as commits in the `checkout` Git repo if there's any

### Build

1. Get the cached diff with git for the `checkout` folder and output the patch file to `.nix-playground/checkout.patch`
2. Insert patch into the payload from `.nix-playground/drv.json`
3. Call `nix derivation add` to add the derivation with patch added
4. Read output patch does not match error, if there's any, patch the derivation payload and jump to step.3 and try again
5. Realize the patched derivation and build

## Roadmap

- Implement `np shell` (like `nix-shell` but with the patches applied)
- Support patching nested dependency package
- Rewrite it with Rust? 🤔
