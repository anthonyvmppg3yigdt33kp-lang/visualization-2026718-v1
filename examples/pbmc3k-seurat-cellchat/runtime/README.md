# Optional Windows shutdown workaround

This folder is not required on a normal R installation.

On the machine used for the 2026-07-18 case, R 4.5.2 and 4.5.3 both completed calculations but crashed during process shutdown with Windows exception `0xC0000005` in `ucrtbase.dll` after loading packages such as `rlang`/`ggplot2`. Source rebuilding packages did not fix the host-level failure.

Only if that exact post-computation shutdown failure is reproduced:

1. Install the Rtools version matching R.
2. From this case directory, compile the helper:

   ```powershell
   Push-Location runtime
   & "$env:R_HOME\bin\R.exe" CMD SHLIB hard_exit.c
   Pop-Location
   ```

3. Set `PBMC3K_WINDOWS_EXIT_WORKAROUND=1` before running a stage.

The helper calls the Windows API `TerminateProcess(..., 0)` only after the stage has written all outputs and a completion marker. It deliberately bypasses normal R shutdown and must not be enabled for an ordinary environment or during interactive analysis. The compiled DLL is host-specific and is therefore not committed.
