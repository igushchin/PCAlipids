import mdtraj as md
import numpy as np
import sys


def lipic(traj_file, top_file, stride):
	traj = md.load_xtc(traj_file, top = top_file, stride = stride)
	traj = traj.superpose(traj[0])
	traj.unitcell_vectors = None
	avg_xyz = traj.xyz.astype(np.float64)
	avg_xyz = avg_xyz.mean(axis = 0, dtype=np.float64)
	avg_traj = md.Trajectory([avg_xyz], traj.top)

	new_traj = md.Trajectory(traj[0].xyz.astype(np.float64) - md.compute_center_of_mass(traj[0]).astype(np.float64), traj[0].top)
	for i in range(1, len(traj)):
		new_traj = new_traj.join(md.Trajectory(traj[i].xyz.astype(np.float64) - md.compute_center_of_mass(traj[i]).astype(np.float64), traj[i].top))
	new_traj = new_traj.superpose(avg_traj)
	new_traj = new_traj.join(avg_traj)
	print(new_traj.xyz.shape)
	return new_traj


def main(traj_file, top_file, stride, mot_out):
	traj = lipic(traj_file, top_file, stride)
	traj.save_pdb(mot_out)
	print('Motion saved in file "%s"' % mot_out)


if __name__ == '__main__':
	args = sys.argv[1:]
	if '-stride' in args:
		stride = int(args[args.index('-stride') + 1])
	else:
		stride = 10000
	if '-om' in args:
		mot_out = args[args.index('-om') + 1]
	else:
		mot_out = 'conform.pdb'
	if '-f' in args and '-t' in args:
		main(args[args.index('-f') + 1], args[args.index('-t') + 1], stride, mot_out)
	elif '-h' not in args and '-help' not in args:
		print('Missing parameters, try -h for flags\n')
	else:
		print('-f <trajectory file> (file format *.xtc)\n-t <topology file> (any file with topology)\n -stride <<positive integer; step of reading frames>\n -om <output file with conformations>')