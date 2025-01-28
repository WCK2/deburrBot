from parts import *
from nos.exception import *

#=================================================
# Generic Main
#=================================================
class GenericMain:
    progs = []
    progsel_gen = True
    def __init__(self,progs=[]) -> None:
        self.progs=progs
    def add(self, progsel, p, **kwargs):
        if type(progsel)==type('1t'): progsel="'%s'" % progsel
        self.progs.append((progsel,p,kwargs))
    def generate(self):
        lines = """"""
        for p in self.progs:
            p[1](**p[2])
            if self.progsel_gen: lines+="# elif p==%s: %s()\n" % (p[0],p[2].get("fn", p[1].__name__))
        lines+="""# else: pass # return prog_ext(p)"""

        lines = """
            \n\n#=================================================
            # Main program select
            #================================================="""+"""
            # def ProgSel(p):
            #     if type(p)==str: p=p.strip()
            #     if p==999: pass
            #     %s
            """ % lines.replace("\n","\n"+" "*16)
        return lines
    def main(self):
        pass

#=================================================
# Generic FN
#=================================================
class DEBURRBOTMAIN(GenericMain):
    def generate(self):
        robot.AddCode(f'from header import *\n')
        robot.AddCode(super().generate())


if __name__ == "__main__":
    try:
        #~ Generate
        if MAKE:
            rdk.setRunMode(RUNMODE_MAKE_ROBOTPROG)
            for header in list(robot.HEADER.__dict__.values())[1:-3]: robot.AddCode(header)
            main = DEBURRBOTMAIN()

            main.add(12, Grind_MS3_CALE10in, frame='Grind_MS3_CALE10in')

            main.generate()

        #~ Simulate
        else:
            rdk.setSimulationSpeed(1.0)

            Grind_MS3_CALE10in(frame='Grind_MS3_CALE10in')



    except:
        print("error")
        exc_info()
    finally: pass
    print("  >> Generation Complete")


