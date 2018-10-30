# GEM5 Benchmark

The archive comes pre-built for x86-64 Linux. On a Unix-like
system with GNU make installed, you can also use 'make clean',
followed by 'make' to rebuild them. You may need to adjust the
supplied Makefile, and the Makefiles in some subdirectories,
if you want to use a compiler other than GCC.

Included in this directory is a script for running gem5 called
gem5script.py.

## Configuration

```bash
ln -s <gem5_installlation_folder> gem5
   ln -s <gem5_installation_folder>/build/X86/gem5.opt ./
```

## Usage
```bash
./gem5.opt gem5script.py --cmd=./blocked-matmul --directory=output
```

The included benchmark is described bellow:

*  blocked-matmul --- does a 84x84 register-blocked matrix multiply.
   Source is in blocked-matmul.c.

