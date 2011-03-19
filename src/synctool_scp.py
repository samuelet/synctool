#! /usr/bin/env python
#
#	synctool-scp	WJ109
#
#   synctool by Walter de Jong <walter@heiho.net> (c) 2003-2011
#
#   synctool COMES WITH NO WARRANTY. synctool IS FREE SOFTWARE.
#   synctool is distributed under terms described in the GNU General Public
#   License.
#
#	- simply use synctool-ssh because lots of code would be the same
#

import synctool_unbuffered
import synctool_config
import synctool_lib
import synctool_ssh

from synctool_lib import verbose,stdout,stderr,unix_out

import os
import sys
import string
import getopt
import shlex

DESTDIR = None
SCP_OPTIONS = None


def run_remote_copy(nodes, files):
	'''copy files[] to nodes[]'''

	if not synctool_config.SCP_CMD:
		stderr('%s: error: scp_cmd has not been defined in %s' % (os.path.basename(sys.argv[0]), synctool_config.CONF_FILE))
		sys.exit(-1)

	files_str = string.join(files)

# prepare cmd_args[] for exec() outside the loop
	cmd_args = shlex.split(synctool_config.SCP_CMD)

	if SCP_OPTIONS:
		cmd_args.extend(shlex.split(SCP_OPTIONS))

	cmd_args.extend(files)

# run scp in serial, not parallel
	for node in nodes:
		if node == synctool_config.NODENAME:
			verbose('skipping node %s' % node)
			continue

		if DESTDIR:
			verbose('copying %s to %s:%s' % (files_str, node, DESTDIR))

			if SCP_OPTIONS:
				unix_out('%s %s %s %s:%s' % (synctool_config.SCP_CMD, SCP_OPTIONS, files_str, node, DESTDIR))
			else:
				unix_out('%s %s %s:%s' % (synctool_config.SCP_CMD, files_str, node, DESTDIR))

		else:
			verbose('copying %s to %s' % (files_str, node))

			if SCP_OPTIONS:
				unix_out('%s %s %s %s:' % (synctool_config.SCP_CMD, SCP_OPTIONS, files_str, node))
			else:
				unix_out('%s %s %s:' % (synctool_config.SCP_CMD, files_str, node))

		if synctool_lib.DRY_RUN:
			continue

		sys.stdout.flush()

		try:
			if not os.fork():
				if DESTDIR:
					cmd_args.append('%s:%s' % (node, DESTDIR))
				else:
					cmd_args.append('%s:' % node)

				try:
					os.execv(cmd_args[0], cmd_args)
				except OSError, reason:
					stderr('failed to execute %s: %s' % (cmd_args[0], reason))

				except:
					stderr('failed to execute %s' % cmd_args[0])

				sys.exit(1)

			else:
				user_interrupt = False
				while True:
					try:
						os.wait()
					except OSError:
						break

					except KeyboardInterrupt:
						user_interrupt = True
						break

				if user_interrupt:
					print
					break

		except KeyboardInterrupt:
			print
			break


def usage():
	print 'usage: %s [options] <filename> [..]' % os.path.basename(sys.argv[0])
	print 'options:'
	print '  -h, --help                     Display this information'
	print '  -c, --conf=dir/file            Use this config file'
	print '                                 (default: %s)' % synctool_config.DEFAULT_CONF
	print '  -n, --node=nodelist            Execute only on these nodes'
	print '  -g, --group=grouplist          Execute only on these groups of nodes'
	print '  -x, --exclude=nodelist         Exclude these nodes from the selected group'
	print '  -X, --exclude-group=grouplist  Exclude these groups from the selection'
	print
	print '  -d, --dest=dir/file            Set destination name to copy to'
	print '  -o, --options=options          Set additional scp options'
	print
	print '  -v, --verbose                  Be verbose'
	print '      --unix                     Output actions as unix shell commands'
	print '      --dry-run                  Do not run the remote copy command'
	print
	print 'A nodelist or grouplist is a comma-separated list'
	print
	print 'synctool-scp by Walter de Jong <walter@heiho.net> (c) 2009-2011'


def get_options():
	global DESTDIR, SCP_OPTIONS

	if len(sys.argv) <= 1:
		usage()
		sys.exit(1)

	DESTDIR = None
	SCP_OPTIONS = None

	try:
		opts, args = getopt.getopt(sys.argv[1:], 'hc:vd:o:n:g:x:X:q', ['help', 'conf=', 'verbose',
			'dest=', 'options=',
			'node=', 'group=', 'exclude=', 'exclude-group=', 'unix', 'dry-run', 'quiet'])
	except getopt.error, (reason):
		print '%s: %s' % (os.path.basename(sys.argv[0]), reason)
#		usage()
		sys.exit(1)

	except getopt.GetoptError, (reason):
		print '%s: %s' % (os.path.basename(sys.argv[0]), reason)
#		usage()
		sys.exit(1)

	except:
		usage()
		sys.exit(1)

	synctool_ssh.NODELIST = ''
	synctool_ssh.GROUPLIST = ''

	for opt, arg in opts:
		if opt in ('-h', '--help', '-?'):
			usage()
			sys.exit(1)

		if opt in ('-c', '--conf'):
			synctool_config.CONF_FILE = arg
			continue

		if opt in ('-v', '--verbose'):
			synctool_lib.VERBOSE = True
			continue

		if opt in ('-d', '--dest'):
			DESTDIR = arg
			continue

		if opt in ('-o', '--options'):
			SCP_OPTIONS = arg
			continue

		if opt in ('-n', '--node'):
			if not synctool_ssh.NODELIST:
				synctool_ssh.NODELIST = arg
			else:
				synctool_ssh.NODELIST = NODELIST + ',' + arg
			continue

		if opt in ('-g', '--group'):
			if not synctool_ssh.GROUPLIST:
				synctool_ssh.GROUPLIST = arg
			else:
				synctool_ssh.GROUPLIST = synctool_ssh.GROUPLIST + ',' + arg
			continue

		if opt in ('-x', '--exclude'):
			if not synctool_ssh.EXCLUDELIST:
				synctool_ssh.EXCLUDELIST = arg
			else:
				synctool_ssh.EXCLUDELIST = synctool_ssh.EXCLUDELIST + ',' + arg
			continue

		if opt in ('-X', '--exclude-group'):
			if not synctool_ssh.EXCLUDEGROUPS:
				synctool_ssh.EXCLUDEGROUPS = arg
			else:
				synctool_ssh.EXCLUDEGROUPS = synctool_ssh.EXCLUDEGROUPS + ',' + arg
			continue

		if opt == '--unix':
			synctool_lib.UNIX_CMD = True
			continue

		if opt == '--dry-run':
			synctool_lib.DRY_RUN = True
			continue

		if opt in ('-q', '--quiet'):
			# silently ignore this option
			continue

	if args == None or len(args) <= 0:
		print '%s: missing file to copy' % os.path.basename(sys.argv[0])
		sys.exit(1)

	return args


if __name__ == '__main__':
	sys.stdout = synctool_unbuffered.Unbuffered(sys.stdout)
	sys.stderr = synctool_unbuffered.Unbuffered(sys.stderr)

	files = get_options()
	synctool_config.read_config()
	synctool_config.add_myhostname()

	nodes = synctool_ssh.make_nodeset()
	if nodes == None or len(nodes) <= 0:
		print 'no valid nodes specified'
		sys.exit(1)

	run_remote_copy(nodes, files)


# EOB
