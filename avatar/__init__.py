"""Package for IntelArk cog"""
from .avatar import AvatarCog


def setup(bot):
    bot.add_cog(AvatarCog(bot))
