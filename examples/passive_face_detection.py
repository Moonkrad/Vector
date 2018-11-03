#!/usr/bin/env python3

import sys
sys.path.insert(1, 'C:\\Users\\MSI USER\\Downloads\\Vector\\vector_python_sdk_0.4.0\\vector_python_sdk_0.4.0')

import functools
import time
from threading import Event

import anki_vector
from anki_vector.events import Events
from anki_vector.util import degrees

faceFound = False

def main():

    def on_robot_observed_face(robot, event_type, event):
        global faceFound
        """on_robot_observed_face is called when a face is seen"""
        print("Vector sees a face")
        for face in robot.world.visible_faces:
            if len(face.name) > 0:
                print(f"Visible face: {face.name}")
                if not faceFound:
                    print(f"Say Text")
                    robot.conn.run_soon(robot.say_text(f"Hello {face.name}"))
                    #name = face.name
                    faceFound = True

    args = anki_vector.util.parse_command_args()
    with anki_vector.Robot(args.serial, enable_vision_mode=True, request_control=False) as robot:
        global faceFound

        robot.faces.enable_vision_mode(1)

        on_robot_observed_face = functools.partial(on_robot_observed_face, robot)
        robot.events.subscribe(on_robot_observed_face, Events.robot_observed_face)

        print("------ waiting for face events, press ctrl+c to exit early ------")

        try:
            # Wait 10 seconds to repeat seeing a face
            while True:
                time.sleep(10)
                faceFound = False
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
