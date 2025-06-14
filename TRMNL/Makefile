.PHONY: serve login push

PWD := $(shell pwd)

serve:
	@ docker run \
		-p 4567:4567 \
		-v "$(PWD)":/plugin \
		trmnl/trmnlp
login:
	@ docker run \
		-it \
		-v "$(PWD)":/plugin \
		trmnl/trmnlp trmnlp login

push:
	@ docker run \
		-v "$(PWD)":/plugin \
		trmnl/trmnlp trmnlp push

.DEFAULT_GOAL := serve
