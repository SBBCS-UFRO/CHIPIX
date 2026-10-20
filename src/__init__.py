# SPDX-License-Identifier: GPL-3.0-or-later
"""CHIPIX bundle entry point. Computational modules do not depend on ChimeraX."""
from chimerax.core.toolshed import BundleAPI
from .branding import TOOL_NAME


class ChipixAPI(BundleAPI):
    api_version = 1

    @staticmethod
    def start_tool(session, bundle_info, tool_info):
        from .tool import ChipixTool
        from chimerax.core.tools import get_singleton
        return get_singleton(session, ChipixTool, tool_info.name, create=True, display=True)

    @staticmethod
    def register_command(bundle_info, command_info, logger):
        from chimerax.core.commands import CmdDesc, register

        def show(session):
            if not session.ui.is_gui:
                from chimerax.core.errors import UserError
                raise UserError("CHIPIX requires the ChimeraX graphical interface.")
            from .tool import ChipixTool
            from chimerax.core.tools import get_singleton
            return get_singleton(session, ChipixTool, TOOL_NAME, create=True, display=True)

        register("chipix", CmdDesc(synopsis="Open CHIPIX"), show, logger=logger)


bundle_api = ChipixAPI()
