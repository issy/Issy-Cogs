"""Package for IntelArk cog"""
from .intelark import IntelArk

def setup(bot):
    bot.add_cog(IntelArk(bot))