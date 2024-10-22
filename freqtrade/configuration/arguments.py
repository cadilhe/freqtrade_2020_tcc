"""
This module contains the argument manager class
"""
import argparse
from functools import partial
from pathlib import Path
from typing import Any, Dict, List, Optional

from freqtrade import constants
from freqtrade.configuration.cli_options import AVAILABLE_CLI_OPTIONS

ARGS_COMMON = ["verbosity", "logfile", "version", "config", "datadir", "user_data_dir"]

ARGS_STRATEGY = ["strategy", "strategy_path"]

ARGS_TRADE = ["db_url", "sd_notify", "dry_run"]

ARGS_COMMON_OPTIMIZE = ["ticker_interval", "timerange",
                        "max_open_trades", "stake_amount", "fee"]

ARGS_BACKTEST = ARGS_COMMON_OPTIMIZE + ["position_stacking", "use_max_market_positions",
                                        "strategy_list", "export", "exportfilename"]

ARGS_HYPEROPT = ARGS_COMMON_OPTIMIZE + ["hyperopt", "hyperopt_path",
                                        "position_stacking", "epochs", "spaces",
                                        "use_max_market_positions", "print_all",
                                        "print_colorized", "print_json", "hyperopt_jobs",
                                        "hyperopt_random_state", "hyperopt_min_trades",
                                        "hyperopt_continue", "hyperopt_loss"]

ARGS_EDGE = ARGS_COMMON_OPTIMIZE + ["stoploss_range"]

ARGS_LIST_EXCHANGES = ["print_one_column", "list_exchanges_all"]

ARGS_LIST_TIMEFRAMES = ["exchange", "print_one_column"]

ARGS_LIST_PAIRS = ["exchange", "print_list", "list_pairs_print_json", "print_one_column",
                   "print_csv", "base_currencies", "quote_currencies", "list_pairs_all"]

ARGS_CREATE_USERDIR = ["user_data_dir", "reset"]

ARGS_BUILD_STRATEGY = ["user_data_dir", "strategy", "template"]

ARGS_BUILD_HYPEROPT = ["user_data_dir", "hyperopt", "template"]

ARGS_DOWNLOAD_DATA = ["pairs", "pairs_file", "days", "download_trades", "exchange",
                      "timeframes", "erase"]

ARGS_PLOT_DATAFRAME = ["pairs", "indicators1", "indicators2", "plot_limit",
                       "db_url", "trade_source", "export", "exportfilename",
                       "timerange", "ticker_interval"]

ARGS_PLOT_PROFIT = ["pairs", "timerange", "export", "exportfilename", "db_url",
                    "trade_source", "ticker_interval"]

NO_CONF_REQURIED = ["download-data", "list-timeframes", "list-markets", "list-pairs",
                    "plot-dataframe", "plot-profit"]

NO_CONF_ALLOWED = ["create-userdir", "list-exchanges", "new-hyperopt", "new-strategy"]


class Arguments:
    """
    Arguments Class. Manage the arguments received by the cli
    """
    def __init__(self, args: Optional[List[str]]) -> None:
        self.args = args
        self._parsed_arg: Optional[argparse.Namespace] = None

    def get_parsed_arg(self) -> Dict[str, Any]:
        """
        Return the list of arguments
        :return: List[str] List of arguments
        """
        if self._parsed_arg is None:
            self._build_subcommands()
            self._parsed_arg = self._parse_args()

        return vars(self._parsed_arg)

    def _parse_args(self) -> argparse.Namespace:
        """
        Parses given arguments and returns an argparse Namespace instance.
        """
        parsed_arg = self.parser.parse_args(self.args)

        # Workaround issue in argparse with action='append' and default value
        # (see https://bugs.python.org/issue16399)
        # Allow no-config for certain commands (like downloading / plotting)
        if ('config' in parsed_arg and parsed_arg.config is None and
            ((Path.cwd() / constants.DEFAULT_CONFIG).is_file() or
             not ('command' in parsed_arg and parsed_arg.command in NO_CONF_REQURIED))):
            parsed_arg.config = [constants.DEFAULT_CONFIG]

        return parsed_arg

    def _build_args(self, optionlist, parser):

        for val in optionlist:
            opt = AVAILABLE_CLI_OPTIONS[val]
            parser.add_argument(*opt.cli, dest=val, **opt.kwargs)

    def _build_subcommands(self) -> None:
        """
        Builds and attaches all subcommands.
        :return: None
        """
        # Build shared arguments (as group Common Options)
        _common_parser = argparse.ArgumentParser(add_help=False)
        group = _common_parser.add_argument_group("Common arguments")
        self._build_args(optionlist=ARGS_COMMON, parser=group)

        _strategy_parser = argparse.ArgumentParser(add_help=False)
        strategy_group = _strategy_parser.add_argument_group("Strategy arguments")
        self._build_args(optionlist=ARGS_STRATEGY, parser=strategy_group)

        # Build main command
        self.parser = argparse.ArgumentParser(description='Free, open source crypto trading bot')
        self._build_args(optionlist=['version'], parser=self.parser)

        from freqtrade.optimize import start_backtesting, start_hyperopt, start_edge
        from freqtrade.utils import (start_create_userdir, start_download_data,
                                     start_list_exchanges, start_list_markets,
                                     start_new_hyperopt, start_new_strategy,
                                     start_list_timeframes, start_trading)
        from freqtrade.plot.plot_utils import start_plot_dataframe, start_plot_profit

        subparsers = self.parser.add_subparsers(dest='command',
                                                # Use custom message when no subhandler is added
                                                # shown from `main.py`
                                                # required=True
                                                )

        # Add trade subcommand
        trade_cmd = subparsers.add_parser('trade', help='Trade module.',
                                          parents=[_common_parser, _strategy_parser])
        trade_cmd.set_defaults(func=start_trading)
        self._build_args(optionlist=ARGS_TRADE, parser=trade_cmd)

        # Add backtesting subcommand
        backtesting_cmd = subparsers.add_parser('backtesting', help='Backtesting module.',
                                                parents=[_common_parser, _strategy_parser])
        backtesting_cmd.set_defaults(func=start_backtesting)
        self._build_args(optionlist=ARGS_BACKTEST, parser=backtesting_cmd)

        # Add edge subcommand
        edge_cmd = subparsers.add_parser('edge', help='Edge module.',
                                         parents=[_common_parser, _strategy_parser])
        edge_cmd.set_defaults(func=start_edge)
        self._build_args(optionlist=ARGS_EDGE, parser=edge_cmd)

        # Add hyperopt subcommand
        hyperopt_cmd = subparsers.add_parser('hyperopt', help='Hyperopt module.',
                                             parents=[_common_parser, _strategy_parser],
                                             )
        hyperopt_cmd.set_defaults(func=start_hyperopt)
        self._build_args(optionlist=ARGS_HYPEROPT, parser=hyperopt_cmd)

        # add create-userdir subcommand
        create_userdir_cmd = subparsers.add_parser('create-userdir',
                                                   help="Create user-data directory.",
                                                   )
        create_userdir_cmd.set_defaults(func=start_create_userdir)
        self._build_args(optionlist=ARGS_CREATE_USERDIR, parser=create_userdir_cmd)

        # add new-strategy subcommand
        build_strategy_cmd = subparsers.add_parser('new-strategy',
                                                   help="Create new strategy")
        build_strategy_cmd.set_defaults(func=start_new_strategy)
        self._build_args(optionlist=ARGS_BUILD_STRATEGY, parser=build_strategy_cmd)

        # add new-hyperopt subcommand
        build_hyperopt_cmd = subparsers.add_parser('new-hyperopt',
                                                   help="Create new hyperopt")
        build_hyperopt_cmd.set_defaults(func=start_new_hyperopt)
        self._build_args(optionlist=ARGS_BUILD_HYPEROPT, parser=build_hyperopt_cmd)

        # Add list-exchanges subcommand
        list_exchanges_cmd = subparsers.add_parser(
            'list-exchanges',
            help='Print available exchanges.',
            parents=[_common_parser],
        )
        list_exchanges_cmd.set_defaults(func=start_list_exchanges)
        self._build_args(optionlist=ARGS_LIST_EXCHANGES, parser=list_exchanges_cmd)

        # Add list-timeframes subcommand
        list_timeframes_cmd = subparsers.add_parser(
            'list-timeframes',
            help='Print available ticker intervals (timeframes) for the exchange.',
            parents=[_common_parser],
        )
        list_timeframes_cmd.set_defaults(func=start_list_timeframes)
        self._build_args(optionlist=ARGS_LIST_TIMEFRAMES, parser=list_timeframes_cmd)

        # Add list-markets subcommand
        list_markets_cmd = subparsers.add_parser(
            'list-markets',
            help='Print markets on exchange.',
            parents=[_common_parser],
        )
        list_markets_cmd.set_defaults(func=partial(start_list_markets, pairs_only=False))
        self._build_args(optionlist=ARGS_LIST_PAIRS, parser=list_markets_cmd)

        # Add list-pairs subcommand
        list_pairs_cmd = subparsers.add_parser(
            'list-pairs',
            help='Print pairs on exchange.',
            parents=[_common_parser],
        )
        list_pairs_cmd.set_defaults(func=partial(start_list_markets, pairs_only=True))
        self._build_args(optionlist=ARGS_LIST_PAIRS, parser=list_pairs_cmd)

        # Add download-data subcommand
        download_data_cmd = subparsers.add_parser(
            'download-data',
            help='Download backtesting data.',
            parents=[_common_parser],
        )
        download_data_cmd.set_defaults(func=start_download_data)
        self._build_args(optionlist=ARGS_DOWNLOAD_DATA, parser=download_data_cmd)

        # Add Plotting subcommand
        plot_dataframe_cmd = subparsers.add_parser(
            'plot-dataframe',
            help='Plot candles with indicators.',
            parents=[_common_parser, _strategy_parser],
        )
        plot_dataframe_cmd.set_defaults(func=start_plot_dataframe)
        self._build_args(optionlist=ARGS_PLOT_DATAFRAME, parser=plot_dataframe_cmd)

        # Plot profit
        plot_profit_cmd = subparsers.add_parser(
            'plot-profit',
            help='Generate plot showing profits.',
            parents=[_common_parser],
        )
        plot_profit_cmd.set_defaults(func=start_plot_profit)
        self._build_args(optionlist=ARGS_PLOT_PROFIT, parser=plot_profit_cmd)
