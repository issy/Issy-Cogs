"""Package for IntelArk cog"""
from .intelark import IntelArk


def setup(bot):
    """Cog entrypoint"""
    bot.add_cog(IntelArk(bot))
