# MetaTrader 5 for Linux systems
This Linux port utilizes the mt5linux [library](https://github.com/lucas-campagna/mt5linux), employing [Wine](https://www.winehq.org), [RPyC](https://github.com/tomerfiliba-org/rpyc), and a Windows version of Python to enable the use of [MetaTrader 5](https://pypi.org/project/MetaTrader5) on Linux.

## Installation

1. Install [Wine](https://wiki.winehq.org/Download).

2. Install [MetaTrader 5 Terminal](https://www.metatrader5.com/en/download)

3. Install [Python for Windows](https://www.python.org/downloads/windows/) within your Wine prefix. Assuming you have downloaded the `python-*.exe` installer:

    ```
    wine cmd
    python-*.exe
    ```

4. Install the [MetaTrader 5](https://www.mql5.com/en/docs/integration/python_metatrader5) library on your **Windows** Python version:

    ```
    wine cmd
    pip install MetaTrader5
    ```

5. Install the packages listed in `requirements.txt` of this directory on both **Linux**:

    ```
    pip install -r requirements.txt
    ```

    and **Windows**:

    ```
    wine cmd
    pip install -r requirements.txt
    ```

## Usage Instructions

Follow these steps:

1. Start pyqtrader:

    ```
    python ./pyqtrader.py
    ```

2. Open the MT5 integration menu: `File -> MT5Integration`.

3. Check the `Enable MetaTrader 5 integration for Linux` box.

4. Locate the `python.exe` file in the Wine prefix and enter the full path to this file.

5. If necessary, provide the full paths to the Wine prefix and the terminal executable (`terminal64.exe`).

6. Save the settings, close pyqtrader, and restart it.

For optimal performance with multiple MT5 terminals, it is advisable to configure a dedicated Wine prefix for the MetaTrader 5 terminal(s) used with pyqtrader MT5 integration. Without this, the integration and other terminals may interfere with each other if installed within the same Wine prefix.

## Headless Mode

This experimental feature allows the MetaTrader 5 terminal to run without a GUI, utilizing a headless mode. This feature requires the installation of the `Xvfb` package on your system. Refer to your distribution's documentation for instructions on installing the `Xvfb` package, which should include an `xvfb-run` wrapper.

To enable this feature, check the respective box in the MT5 integration menu.
