from multiprocessing import process, queue
#import here the function reading serial and the one sending data through wifi #

# crée une queue de taille 10
q = multiprocessing.queue(10)

reader_process = process(target=reader, args=(q,))
reader_process.daemon = True
reader_process.start()        # Launch reader() as a separate python process

# writer_process = process(targer=, args=(q,))
# writer_process.daemon = True
# writer_process.start()

reader_process.join()
