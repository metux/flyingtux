
all:	srv cli

ILIB=ipcproto.c

srv:	srv.c $(ILIB)
	$(CC) -o $@ $< $(ILIB)

cli:	cli.c $(ILIB)
	$(CC) -o $@ $< $(ILIB)

clean:
	rm -f *.o srv cli
