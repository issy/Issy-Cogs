"""Package for IntelArk cog"""
from .intel-ark import IntelArk

def setup(bot):
    bot.add_cog(IntelArk(bot))