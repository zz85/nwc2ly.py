example.pdf : example.ly
	lilypond example.ly

example.ly : example.nwc nwc2ly.py nwc2ly.ini
	./nwc2ly.py example.nwc example.ly

clean :
	rm example.ly example.pdf uncompressed.nwc
