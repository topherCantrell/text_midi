import pygame
import pygame.midi

pygame.init()
pygame.midi.init()

for x in range(0, pygame.midi.get_count()):
    print pygame.midi.get_device_info(x)

inp = pygame.midi.Input(1)

while True:
    if inp.poll():
        print inp.read(1000)
        pygame.time.wait(10)