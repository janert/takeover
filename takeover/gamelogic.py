
import math
import random

# Players, Planets, Fleets hold objects of each other.
# Use integer indices only in the interface to the UI.
#
# Players and Planets hold references of each other. Only two assignments:
# - At creation, each Player gets a homeplanet.
# - Thereafter, ownership only changes in battles.
#
# Fleet and Player objs hold refs of each other. 
# Fleets hold refs to src and dst planets, but do not change their owners (?)

class Player:
    def __init__( self, name, homeplanet, is_human=False ):
        self.name = name
        self.planets = { homeplanet:1 }
        self.fleets = []

        self.is_human_ = is_human
        
    def is_human( self ):
        return self.is_human_
        
    def is_active( self ):
        # only if has_planets or has_fleet
        return len(self.planets) > 0 or len(self.fleets) > 0

    def relinquish_planet( self, planet ):
        del self.planets[planet]

    def accept_planet( self, planet ):
        self.planets[planet] = 1

    def launch_fleet( self, src, dst, ships, sprite=None ):
        fleet = Fleet( self, src, dst, ships, sprite )
        self.fleets.append( fleet )

        # print( "%s %s -> %s : %d" % ( self.name, src.name, dst.name, ships ) )
                      

    def remove_fleet( self, fleet ):
        self.fleets.remove(fleet)
                
    def make_move( self, planets ):
        # for all owned planets
        for p in self.planets:
            # for all neighbors
            for q in p.sorted_neighbors:
                # no self-interaction, no attacks on owned planets
                if p == q or q.owner == self:
                    continue

                # don't attack if not enough ships:
                if 0.7*p.ships < random.randint( 15, 50 ):
                    continue
                
                # rm planets I already attack
                if any( f.dst == q for f in self.fleets ):
                    continue

                # ... attack
                if q.ships < 0.7*p.ships:
                    self.launch_fleet( p, q, int(0.7*p.ships) ) 

        # for f in self.fleets: print( f )

    def stats( self ):
        planets = len(self.planets)
        
        ships = sum( [ p.ships for p in self.planets] )
        ships += sum( [ f.ships for f in self.fleets] )

        prod, strength = 0, 0
        if planets > 0:
            prod = sum( [ p.prod for p in self.planets] )
            strength = sum([p.strength for p in self.planets])/planets

        power = sum( [ p.ships*p.strength for p in self.planets ] )
        power += sum( [ f.ships*f.strength for f in self.fleets ] )

        return [ " " + self.name, planets, "%d" % ships,
                 "%d" % power, "%d" % prod, "%.2f" % strength ]

    
class Planet:
    def __init__( self, pos, is_home=False ):
        self.name = "unk"
        self.owner = None
        self.pos = pos
        if is_home == True:
            self.prod = 10
            self.strength = 0.4
        else:
            self.prod = random.randint( 5, 15 )        
            self.strength = random.uniform( 0.1, 1.0 )
        self.ships = self.prod
        
    def find_distances( self, planets ):
        distances = {}
        
        for p in planets:
            r = math.hypot( p.pos[0]-self.pos[0], p.pos[1]-self.pos[1] )
            distances[ p ] = r

        self.sorted_neighbors = sorted( distances, key=lambda _: distances[_] )
        
    def propagate( self ):
        if self.owner is not None:
            self.ships += self.prod     # could be randomized

    def change_owner( self, player ):
        if self.owner is not None:
            self.owner.relinquish_planet( self )
            
        self.owner = player
        self.owner.accept_planet( self )
            
    def stats( self ):
        owner = self.owner.name if self.owner else " "
        return [ " "+self.name, owner, "%d" % self.ships, "%d" % self.prod,
                 "%.2f" % self.strength, "%.2f" % (self.prod*self.strength) ]

    
class Fleet:
    def __init__( self, owner, src, dst, ships, sprite=None ):
        self.owner = owner
        self.src = src      # unused as member, could be cut
        self.dst = dst
        self.ships = ships
        self.pos = src.pos
        self.strength = src.strength

        self.src.ships -= ships   # very important!
        
        self.sprite = sprite
        self.offset = 15          # half planet width!
        
        speed = 15.0
        vx = dst.pos[0] - src.pos[0]
        vy = dst.pos[1] - src.pos[1]
        v = math.hypot( vx, vy )
        self.velocity = ( speed*vx/v, speed*vy/v ) if v > 0 else 0

        # Make an initial step in direction; to get away from planet
        self.pos = ( self.pos[0] + 1.75*self.velocity[0],
                     self.pos[1] + 1.75*self.velocity[1] )
        
        if sprite:
            phi = 180*math.atan2( vx/v, vy/v )/math.pi
            self.sprite.update( x=self.pos[0]+self.offset,
                                y=self.pos[1]+self.offset,
                                rotation=phi )

    def __str__( self ):
        return "%s : %d : %s -> %s" % ( self.owner.name, self.ships,
                                        self.src.name, self.dst.name )
        
    def propagate( self ):
        self.pos = ( self.pos[0] + self.velocity[0],
                     self.pos[1] + self.velocity[1] )

        if math.hypot( self.dst.pos[0] - self.pos[0],
                       self.dst.pos[1] - self.pos[1] ) < 20:
            # attack
            if self.sprite:
                self.sprite.delete()
            self.owner.remove_fleet( self )
            return True
        
        if self.sprite:
            self.sprite.update( x=self.pos[0]+self.offset,
                                y=self.pos[1]+self.offset )

        return False
        
    def fight( self ):
        # Don't fight if same owner
        if self.owner == self.dst.owner:
            self.dst.ships += self.ships
            return True # is friendly landing, not attack

        # Different owners: fight
        attack = self.ships
        defense = self.dst.ships

        while attack > 0 and defense > 0:
            r = random.uniform( 0, self.strength + self.dst.strength )
            
            if r < self.strength:
                defense -= 1
            else:
                attack -= 1

            # print( attack, ">", defense )

        """
        print( "%s %d > %d : %d > %d (%d,%d)" % ( self.owner.name, 
                                                  self.ships, self.dst.ships,
                                                  attack, defense,
                                                  self.pos[0], self.pos[1] ) )
        """

        # Attack failed, nothing further to do
        if attack == 0:
            self.dst.ships = defense
            return False

        # Attack succeeded, change planet owner
        self.dst.change_owner( self.owner )       
        self.dst.ships = attack       # remaining ships from fleet

        return False
        

class Game:
    def __init__( self, players, planets, buttons, fleet_mkr, battle_mkr,
                  support_mkr, positions, tbl1, tbl2 ):
        self.planets = []
        self.players = []

        self.fleet_maker = fleet_mkr
        self.battle_maker = battle_mkr
        self.support_maker = support_mkr
        
        # Index into positions[] is advanced "manually" three times below!
        random.shuffle( positions )
        
        # Players and Planets
        # First player (i=0) is human
        p = Planet( positions[0], is_home=True )
        self.players.append( Player( "human", p, is_human=True ) )
        p.owner = self.players[-1]
        self.planets.append( p )

        # Players and their homeplanets
        for i in range( players ):
            p = Planet( positions[1+i], is_home=True )
            self.players.append( Player( "AI%0d" % i, p ) )
            p.owner = self.players[-1]            
            self.planets.append( p )
            
        # Neutral Planets
        for i in range( planets ):
            self.planets.append( Planet( positions[1+players+i] ) )

        # All planets need to know distances to each other:
        for p in self.planets:
            p.find_distances( self.planets )

        # Update UI planets with position info; grab the names from UI buttons
        for i in range( len(self.planets) ):
            buttons[i].x = self.planets[i].pos[0]
            buttons[i].y = self.planets[i].pos[1]
            
            self.planets[i].name = buttons[i].name

            # print( self.planets[i].name, self.planets[i].pos )
            
        # Populate tables : direct copy from propagate()
        for row, p in enumerate(self.players):
            for col, s in enumerate(p.stats()):
                tbl1.set_text( 1+row, col, str( s ) ) 

        for row, p in enumerate(self.planets):
            stats = p.stats()
            for col, s in enumerate(p.stats()):
                tbl2.set_text( 1+row, col, str( s ) )

            
    # kbd event
    def propagate( self, tbl1, tbl2 ):
        for p in self.planets:
            p.propagate()

        shuffled_players = list( range( len(self.players) ) )
        random.shuffle( shuffled_players )
        
        for i in shuffled_players:
            for f in self.players[i].fleets:
                arrived = f.propagate()

                # if arrived: fight
                if arrived:
                    is_support = f.fight()
                    

                    if is_support:
                        support = self.support_maker( x=f.dst.pos[0]+15-24,
                                                      y=f.dst.pos[1]+15-24 )
                    else:
                        # offset: 15=half planet width; 24=half explosion width
                        battle = self.battle_maker( x=f.dst.pos[0]+15-24,
                                                    y=f.dst.pos[1]+15-24 )
                    
                    
        for i in shuffled_players:
            if self.players[i].is_active() and not self.players[i].is_human():
                self.players[i].make_move( self.planets ) 
            
        # pass info to display - remember: room for header line!
        for row, p in enumerate(self.players):
            for col, s in enumerate(p.stats()):
                tbl1.set_text( 1+row, col, str( s ) ) 

        for row, p in enumerate(self.planets):
            stats = p.stats()
            for col, s in enumerate(p.stats()):
                tbl2.set_text( 1+row, col, str( s ) )

        # check for game over
        alive_players = 0
        for p in self.players:
            if len(p.planets) + len(p.fleets) > 0:
                alive_players += 1
                
        return alive_players
            

    # Used to activate slider
    def is_owned_by_human( self, idx ):
        if self.planets[idx].owner is None:
            return False
        return self.planets[idx].owner.is_human()

    
    # Used to populate slider
    def ships_on_planet( self, idx ):
        return self.planets[idx].ships

    
    # Used to launch a fleet from the UI (player is always human!)
    def launch_fleet( self, src_idx, dst_idx, size ):
        if size == 0:
            return

        src = self.planets[src_idx]
        dst = self.planets[dst_idx]

        self.players[0].launch_fleet( src, dst, size, 
                                      sprite=self.fleet_maker() )
