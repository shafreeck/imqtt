from IPython.terminal.embed import InteractiveShellEmbed

banner = """Welcome to imqtt !
An iteractive MQTT packet manipulation shell based on IPython.
Github: https://github.com/shafreeck/imqtt
"""
tips = """
This is an interactive environment, and being triggered when there was a packet received.
There are some varibles you can use:
 self: the tcp server object
 buf : current data received
 p   : the packet that unmarshaled from buf 
Also, all python features are avaliable. Type 'exit()' or press 'Ctrl-D' to quit the shell.
"""

ipshell = InteractiveShellEmbed(banner1= banner, exit_msg= 'Bye!')
enter = InteractiveShellEmbed(banner1 = 'Packet received', banner2 = tips, exit_msg = 'Continue to serve...')
