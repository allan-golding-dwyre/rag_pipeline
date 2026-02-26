FROM ubuntu:latest
LABEL authors="agolding@france.groupe.intra"

ENTRYPOINT ["top", "-b"]