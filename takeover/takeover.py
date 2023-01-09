
import random

import pyglet

# if run as a script, pull from local directory
# otherwise (if run as module), pull from package
if __name__ == "__main__":
    import utils
    import gamelogic
else:
    from . import utils
    from . import gamelogic
    # import takeover.utils as utils
    # import takeover.gamelogic as gamelogic
    
    
class SplashController( utils.Controller ):
    def __init__( self, win ):
        self.window = win
        self.frame = utils.Frame( win )
        self.batch = pyglet.graphics.Batch()

        self.bg = pyglet.shapes.Rectangle( 0, 0, win.width, win.height,
                                           color=(255,255,255) )
        self.splash = pyglet.resource.image( "splash2.png" )

        
        # --- Text
        doc = pyglet.resource.text( "welcome.txt" )
        doc.set_style( 0, 0,  { "color": (0,255,0,255), "align": "left" } )
        self.layout = pyglet.text.layout.TextLayout( doc, 600, 250,
                                                     multiline=True,
                                                     wrap_lines=True,
                                                     batch=self.batch )
        self.layout.x, self.layout.y = 180+10, 285
        
        
        # --- Slider
        bar = pyglet.resource.image( "metal-bar-320x40.png" )
        knob = pyglet.resource.image( "metal-knob-36x36.png" )        
        self.slider1 = utils.LabeledSlider( 60, 80, bar, knob, edge=0,
                                            batch=self.batch )
        self.slider2 = utils.LabeledSlider( 580, 80, bar, knob, edge=0,
                                            batch=self.batch )
        self.slider1.update( "Opponents", 5, 1, 10 )
        self.slider2.update( "Neutral Planets", 7, 1, 12 )
        
        self.frame.add_widget( self.slider1 )
        self.frame.add_widget( self.slider2 )        
       

        # --- Button
        imgs = []
        for name in [ "redDown.png", "greenNormal.png", "redNormal.png" ]:
            imgs.append( pyglet.resource.image( name ) )

        # Images: pressed, unpressed, hover (!!!)
        self.button = utils.HoverButton( win.width//2 - imgs[0].width//2,
                                         80 - imgs[0].height//2, *imgs,
                                         batch=self.batch )
        self.button.set_scale( 1.0 )
        self.frame.add_widget( self.button )
        
        def clicked():
            self.frame.remove_widget( self.button )
            self.frame.remove_widget( self.slider1 )
            self.frame.remove_widget( self.slider2 )
            self.batch.invalidate()
            self.window.pop_handlers() # This pops the frame!
            self.window.set_controller( GameController(self.window,
                                                       self.slider1.result,
                                                       self.slider2.result) )
        self.button.on_click = clicked
        
    def draw( self ):        
        self.window.clear()
        self.bg.draw()
        self.splash.blit( 0, 0 )
        self.batch.draw()

        
class PlanetButton( utils.HoverButton ):
    def __init__( self, idx, img, batch, group ):
        super().__init__( -100, -100, img, img, batch=batch, group=group )
        self.idx = idx
        
    def on_mouse_press( self, x, y, buttons, modifiers ):
        if self._check_hit( x, y ):
            self.dispatch_event( "on_dn",
                                 self.x+self.width//2, self.y+self.height//2,
                                 self.idx )

    def on_mouse_release( self, x, y, buttons, modifiers ):
        if self._check_hit( x, y ):
            self.dispatch_event( "on_up", self.x, self.y, self.idx )

PlanetButton.register_event_type( "on_dn" )
PlanetButton.register_event_type( "on_up" )


class GameController( utils.Controller ):
    def __init__( self, win, opponents, planets ):
        self.window = win
        self.frame = utils.Frame( self.window )
        self.batch = pyglet.graphics.Batch()

        planet_grp = pyglet.graphics.Group(0)
        fleets_grp = pyglet.graphics.Group(1)
        effect_grp = pyglet.graphics.Group(2)

        self.over = None

        metal = pyglet.resource.image( "panel2.png" )
        # metal = pyglet.resource.image( "panel5.png" )
        # metal = pyglet.resource.image( "panel4.png" )
        self.metal = pyglet.sprite.Sprite( metal, x=640, y=0 )

        
        # Slider
        self.slider = None
        self.bar = pyglet.resource.image( "metal-bar-320x40.png" )
        self.knob = pyglet.resource.image( "metal-knob-36x36.png" )        
        
        
        # Background
        self.bg = pyglet.resource.image( "background-640x640.png" )
        self.upp = pyglet.sprite.Sprite( self.bg, batch=self.batch )
        self.low = pyglet.sprite.Sprite( self.bg, batch=self.batch )
        self.seam = 0

        pyglet.clock.schedule_interval(self.scroll_background, 1/60.)
        
        
        # Opponent Table
        # name, planets, ships, power, prod, strength
        rows = 1 + 1 + opponents # header + human + opps
        self.table1 = utils.TextTable( rows, 15, [50, 45, 40, 45, 55, 55],
                                       background=(220,220,220), fontsize=10 )
        self.table1.set_position( 10+self.bg.width, 
                                  self.window.height - rows*15 - 10 + 1)
        hdr = [ "Name", "Planets", "Ships", "Power", "Ttl Prod", "Avg Strng"]
        for row, h in enumerate(hdr):
            self.table1.set_attr( 0, row, text=h, bold=True, size=7 )

        # Planet Table
        # name, owner, ships, prod, strength
        rows = 1 + 1 + opponents + planets # hdr + human + opps + neutral
        self.table2 = utils.TextTable( rows, 15, [60,55,40,35,55,45],
                                       background=(220,220,220), fontsize=10 )
        self.table2.set_position( 10+self.bg.width, 10 - 1 )
        hdr = [ "Name", "Owner", "Ships", "Prod", "Strngth", "Value" ]
        for row, h in enumerate(hdr):
            self.table2.set_attr( 0, row, text=h, bold=True, size=8 )


        # Instructions
        doc = pyglet.resource.text( "help.txt" )
        doc.set_style( 0, 0, { "color": (0,255,0,255), "font_size": 10 } )
        self.layout = pyglet.text.layout.TextLayout( doc, 300, 90,
                                                     multiline=True,
                                                     wrap_lines=False,
                                                     batch=self.batch )
        
        space = self.window.height - 15*(opponents+2) - 10 - 15*rows - 10
        self.layout.x = 10 + self.bg.width
        self.layout.y = 10+15*rows + space//2 - 90//2 - 1
        
                
        # Fleets
        # fleet_img = pyglet.resource.image( "icons8-launch-30.png" )
        fleet_img = pyglet.resource.image( "icons8-viper-mark-2-24.png" )
        fleet_img.anchor_x = fleet_img.width//2
        fleet_img.anchor_y = fleet_img.height//2
        self.fleets = {}

        def fleet_maker():
            fleet = pyglet.sprite.Sprite( fleet_img, batch=self.batch,
                                          group=fleets_grp )
            self.fleets[ fleet ] = 1
            def f():
                del self.fleets[fleet] # self is the game obj!
                fleet.delete()
            fleet.remove = f
            return fleet

        
        # Battles
        tmp = pyglet.image.ImageGrid( pyglet.resource.image("explosion.png"),
                                      1, 15 )
        tmp = pyglet.image.Animation.from_image_sequence( tmp,
                                                          duration=0.1,
                                                          loop=False )
        
        battle_img = tmp
        self.battles = {}
        
        def battle_maker( x, y ):
            battle = pyglet.sprite.Sprite( battle_img, x=x, y=y,
                                           batch=self.batch,
                                           group=effect_grp )
            self.battles[ battle ] = 1
            def f():
                del self.battles[battle]
                battle.delete()
            battle.on_animation_end = f  # sprite removes itself when done!
            return battle


        # Reinforcements
        tmp = pyglet.image.ImageGrid( pyglet.resource.image("expanding.png"),
                                      1, 8 )
        tmp = pyglet.image.Animation.from_image_sequence( tmp,
                                                          duration=0.1,
                                                          loop=False )
        support_img = tmp
        self.supports = {}
        
        def support_maker( x, y ):
            support = pyglet.sprite.Sprite( support_img, x=x, y=y,
                                           batch=self.batch,
                                           group=effect_grp )
            self.supports[ support ] = 1
            def f():
                del self.supports[ support ]
                support.delete()
            support.on_animation_end = f  # sprite removes itself when done!
            return support
        
        
        # Planets
        # PlanetButtons are UI (complex) objects, because they perform all
        # the event handling; they are not mere sprites. They therefore have
        # a separate existence from the gamelogic Planets. All possible
        # PlanetButtons are created at once and kept; it's up to gamelogic
        # to place the required number on the screen (the rest is not shown)
        # Names should be not more than 7 chars!
        names = []
        for line in pyglet.resource.text( "names.txt" ).text.split( "\n" ):
            if line:
                name = line.strip()
                names.append( name )
        random.shuffle( names )
        
        self.planets = []        
        for i in range(0,26):
            k = 1 + i%17
            planet_img = pyglet.resource.image( "planets/planet%02d.png"%k )
            but = PlanetButton( i, planet_img, self.batch, planet_grp )
            but.set_scale( 0.1 )

            # Monkey patch the name onto the planet
            but.name = names[i]

            # capture crr val of i, with room for header
            def f( i=i+1 ): self.table2.highlight(i) 
            but.on_enter = f
            but.on_leave = f
            but.push_handlers( self.on_dn, self.on_up )
            
            self.planets.append( but )
            self.frame.add_widget( but )
            
            if len(self.planets) == planets + opponents + 1:
                break

            
        # Drag-n-Drop 
        self.rubber = None
        self.src, self.dst = None, None


        # Load a set of non-overlapping random positions,
        # generated using Bridson's Blue Noise algo
        positions = []
        for line in pyglet.resource.text( "positions.txt" ).text.split( "\n" ):
            if line:
                x, y = line.strip().split( "\t" )
                positions.append( (float(x), float(y)) )            
                
                
        # Finally, instantiate gamelogic, now that UI is all set up        
        self.game = gamelogic.Game( opponents, planets, self.planets,
                                    fleet_maker, battle_maker, support_maker,
                                    positions, self.table1, self.table2 )
        
    def on_dn( self, x, y, i ):
        if self.slider:
            return
        
        # only do if owned by human!
        if not self.game.is_owned_by_human( i ):
            return
        
        self.rubber = pyglet.shapes.Line( x, y, x, y,
                                          width=3, color=(0,255,0,128),
                                          batch=self.batch )
        self.src = i
        
    def on_up( self, x, y, i ):
        if self.src is None:
            return
        
        self.rubber = None
        self.dst = i

        if self.src == self.dst:
            self.src, self.dst = None, None
            return
      
        # print( self.src, "->", self.dst )
        # self.src, self.dst = None, None

        ships = self.game.ships_on_planet( self.src )
        
        self.slider_batch = pyglet.graphics.Batch()
        self.slider = utils.LabeledSlider( 160, 50, self.bar, self.knob,
                                           edge=0, batch=self.slider_batch )
        self.slider.update( "Ships", ships//2, 0, ships )
        self.slider.push_handlers( on_up=self.launch_fleet )
        self.frame.add_widget( self.slider )

    def launch_fleet( self, v ):
        # print( self.src, "->", self.dst, ":", v )

        self.frame.remove_widget( self.slider )
        self.slider_batch.invalidate()
        self.slider = None

        self.game.launch_fleet( self.src, self.dst, v )
        
        self.src, self.dst = None, None # this may not be necessary!        
        
    # window event, not button event!
    def on_mouse_drag( self, x, y, dx, dy, but, mod ):
        if self.rubber:
            self.rubber.x2 = x
            self.rubber.y2 = y

    # window event, not button event!            
    def on_mouse_release( self, x, y, but, mod ):
        if self.rubber:
            self.rubber = None

            
    def on_key_press( self, sym, mod ):
        if self.slider:
            if sym == pyglet.window.key.RETURN:
                self.launch_fleet( self.slider.result )
            else:
                return
        
        if sym == pyglet.window.key.SPACE:
            alive_players = self.game.propagate( self.table1, self.table2 )

            if alive_players == 1:
                pyglet.clock.unschedule(self.scroll_background)
                
                # self.window.pop_handlers() # This pops the frame!
                # self.window.set_controller( EndController(self.window) )

                self.over = pyglet.text.Label( "Game Over!",
                                               x=640//2,
                                               y=self.window.height//2,
                                               anchor_x = "center",
                                               color=(0,255,0,255),
                                               font_size=24 )
                
    def scroll_background( self, dt ):
        self.seam = ( self.bg.height + self.seam - 10*dt )%self.bg.height

        self.upp.image = self.bg.get_region( 0, self.seam, self.bg.width,
                                             self.bg.height - self.seam )
        self.low.image = self.bg.get_region( 0, 0, self.bg.width, self.seam )
        self.low.y = self.bg.height - self.seam

        
    def draw( self ):
        self.window.clear()
        pyglet.shapes.Rectangle( self.bg.width+1, 0, 
                                 self.window.width-self.bg.width-1,
                                 self.window.height,
                                 color=(223,224,228) ).draw()        
        self.metal.draw()
        
        self.table1.draw()
        self.table2.draw()

        self.batch.draw()
        
        if self.slider is not None:
            self.slider_batch.draw()

        if self.over:
            self.over.draw()


# Unused...            
class EndController( utils.Controller ):
    def __init__( self, win ):
        self.window = win
        
        self.bg = pyglet.shapes.Rectangle( 0, 0, win.width, win.height,
                                           color=(255,255,255) )
        
        self.label = pyglet.text.Label( "Game Over!",
                                        x=640//2, y=win.height//2,
                                        anchor_x = "center",
                                        color=(0,255,0,255), font_size=24 )

    def draw( self ):        
#        self.window.clear()
#        self.bg.draw()
        self.label.draw()
    
            
# -----

def main():
    # NOTE:
    # The resources "module" MUST have an __init__.py file (even if empty)
    # for the resource lookup logic to work!
    pyglet.resource.path = [ "resources", "@takeover.resources" ]

    win = utils.MainWindow( width=960, height=640, caption="TakeOver" )
    win.set_controller( SplashController(win) )
    # win.set_controller( GameController(win,1,1) )

    pyglet.app.run()


if __name__ == "__main__":
    main()
