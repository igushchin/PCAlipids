import matplotlib.pyplot as plt
import numpy as np
from multiprocessing import Pool
import sys
import math


def estimated_autocorrelation(x):
	n = len(x)
	variance = x.var()
	x = x-x.mean()
	r = np.correlate(x, x, mode = 'full')[-n:]
	assert np.allclose(r, np.array([(x[:n-k]*x[-(n-k):]).sum() for k in range(n)]))
	result = r/(variance*(np.arange(n, 0, -1)))
	return result


def get_nearest_value(iterable, value):
	for idx, x in enumerate(iterable):
		if x < value:
			break
	B = idx
	if idx - 1 == -1:
		A = idx + 1
	else:
		A = idx - 1
	return A, B


def calc(filename, N_lips, timestep):
	file = open(filename, 'r')
	data = []
	for line in file:
	    if line.find('@') == -1 and line.find('&') == -1:
	        data.append(np.float(line.split()[0]))
	    if line.find('&') != -1:
	        break
	file.close()
	data = np.array(data, dtype = np.float64)
	data_1 = data[:len(data) // N_lips]
	R = estimated_autocorrelation(data_1)
	for i in range(1, N_lips):
	    data_1 = data[len(data) * i // N_lips:len(data) * (i + 1) // N_lips]
	    R += estimated_autocorrelation(data_1)
	R /= N_lips
	T = []
	for i in range(1, len(R) + 1):
	    T.append(timestep * i)
	print(filename + ' - processed')
	return T, R


def main(filenames, N_lips, timestep, file_out = 'autocorr_relaxtime_vs_PC.xvg'):
	input_data = [(filename, N_lips, timestep) for filename in filenames]
	with Pool(8) as p:
		data = p.starmap(calc, input_data)
	for idx, obj in enumerate(data):
		T = obj[0]
		R = obj[1]
		plt.loglog(T, R, color = [0, 0, 1 - idx / len(data)])
	plt.ylim([0.001, 1])
	plt.xlabel('Time (ns)')
	plt.ylabel('Autocorrelation')
	plt.show()

	file = open(file_out, 'w')
	file.write('### Autocorr ###\n')
	file.write('E**2\n')

	handles = []

	PC = []
	T_relax = []

	for i, value in enumerate(data):
		T = value[0]
		R = value[1]
		A,B = get_nearest_value(R,math.e ** (-2))
		a = (T[B] - T[A]) / (R[B] - R[A])
		b = T[A] - a * R[A]
		t_relax = a * math.e ** (-2) + b
		PC.append(i + 1)
		T_relax.append(t_relax)

	p = plt.loglog(PC, T_relax, label = r'$\tau_2 = 1/e^2$', color = 'blue', linestyle = '--')
	handle, = p 
	handles.append(handle)

	for i in range(len(PC)):
		file.write(str(PC[i]) + ' ' + str(T_relax[i]))
		file.write('\n')
	file.write('\n')

	PC = []
	T_relax = []

	for i, value in enumerate(data):
		T = value[0]
		R = value[1]
		A, B = get_nearest_value(R, math.e ** (-1))
		a = (T[B] - T[A]) / (R[B] - R[A])
		b = T[A] - a * R[A]
		t_relax = a * math.e ** (-1) + b
		PC.append(i + 1)
		T_relax.append(t_relax)


	file.write('E**1\n')
	for i in range(len(PC)):
		file.write(str(PC[i]) + ' ' + str(T_relax[i]))
		file.write('\n')
	file.close()


	p = plt.loglog(PC, T_relax, label = r'$\tau_1 = 1/e$', color = 'blue', linestyle = '-')
	handle, = p
	handles.append(handle)
	plt.ylim([0.01, 10 ** 3])
	plt.ylabel('Relaxation time (ns)')
	plt.xlabel('Component')
	plt.legend(handles = handles)
	plt.show()


if __name__ == '__main__':
	args = sys.argv[1:]
	if '-p' in args and '-ln' in args and '-dt' in args and '-o' in args and '-pr' not in args:
		filenames = [args[i] for i in range(args.index('-p') + 1, args.index('-o'))]
		main(filenames, int(args[args.index('-ln') + 1]), float(args[args.index('-dt') + 1]), args[args.index('-o') + 1])
	elif '-p' in args and '-ln' in args and '-dt' in args and '-o' not in args and '-pr' not in args:
		print('No output file supplied. Data will be written in "autocorr_relaxtime_vs_PC.xvg"')
		filenames = [args[i] for i in range(args.index('-p') + 1, args.index('-o'))]
		main(filenames, int(args[args.index('-ln') + 1]), float(args[args.index('-dt') + 1]))
	elif '-pr' in args and '-ln' in args and '-dt' in args and '-o' in args and '-p' not in args:
		files = args[args.index('-pr') + 1]
		file_start = files[:files.find('-')]
		file_end = files[files.find('-') + 1:]
		start = int(''.join(filter(lambda x: x.isdigit(), file_start)))
		end = int(''.join(filter(lambda x: x.isdigit(), file_end)))
		file_mask = ''.join(filter(lambda x: not x.isdigit(), file_start))
		filenames = [file_mask[:file_mask.find('.')] + str(i) + file_mask[file_mask.find('.'):] for i in range(start, end + 1)]
		main(filenames, int(args[args.index('-ln') + 1]), float(args[args.index('-dt') + 1]), args[args.index('-o') + 1])
	elif '-pr' in args and '-ln' in args and '-dt' in args and '-o' not in args and '-p' not in args: 
		files = args[args.index('-pr') + 1]
		file_start = files[:files.find('-')]
		file_end = files[files.find('-') + 1:]
		start = int(''.join(filter(lambda x: x.isdigit(), file_start)))
		end = int(''.join(filter(lambda x: x.isdigit(), file_end)))
		file_mask = ''.join(filter(lambda x: not x.isdigit(), file_start))
		filenames = [file_mask[:file_mask.find('.')] + str(i) + file_mask[file_mask.find('.'):] for i in range(start, end + 1)]
		main(filenames, int(args[args.index('-ln') + 1]), float(args[args.index('-dt') + 1]))
	elif '-h' not in args:
		print('Missing parameters, try -h for flags\n')
	else:
		print('-p <sequence of projection files>\n -pr <range of files: "proj1.xvg-proj100.xvg">\n-t <topology file> (any file with topology)\n-r <reference traj file> (any file with 1 ref frame). If not supplied, \
			the first frame of trajectory will be used for alignment.')

