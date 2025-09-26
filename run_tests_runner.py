import runpy, sys
sys.path.insert(0, r'D:\Alien-invasion')
print('Running intercept test')
runpy.run_path(r'D:\Alien-invasion\tests\test_intercept_solver.py', run_name='__main__')
print('Intercept test finished')
print('Running fire parity test')
runpy.run_path(r'D:\Alien-invasion\tests\test_fire_parity.py', run_name='__main__')
print('Fire parity test finished')
