"""Shared authoring coordinates, metres. Does not modify the map on import."""
import json, math, pathlib
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[2]
ORIGIN=(2078.0,2271.0)
ACROSS=(.75,.6614378277661477)
BACK=(-ACROSS[1],ACROSS[0])
META=json.loads((ROOT/'wolmyeongdong/assets/core/geography.json').read_text())
IMAGE=Image.open(ROOT/'wolmyeongdong/assets/core/heightmap-rg16.png')
def world(u,v):return ORIGIN[0]+u*ACROSS[0]+v*BACK[0],ORIGIN[1]+u*ACROSS[1]+v*BACK[1]
def ground(x,y):
 x0,y0,_=META['terrain_position'];u=max(0,min(1024,(x-x0)/META['width_m']*1024));v=max(0,min(1024,(y-y0)/META['height_m']*1024));i,j=min(1023,int(u)),min(1023,int(v));a,b=u-i,v-j
 def grid(c,r):
  uu,vv=c/2,r/2;ii,jj=min(511,int(uu)),min(511,int(vv));aa,bb=uu-ii,vv-jj
  def pix(i,j):red,green,_=IMAGE.getpixel((i,j));return (red*256+green)/65535*600
  return pix(ii,jj)*(1-aa)*(1-bb)+pix(ii+1,jj)*aa*(1-bb)+pix(ii,jj+1)*(1-aa)*bb+pix(ii+1,jj+1)*aa*bb
 tl,tr,bl,br=grid(i,j),grid(i+1,j),grid(i,j+1),grid(i+1,j+1)
 return tl+a*(tr-tl)+b*(bl-tl) if a+b<=1 else br+(1-a)*(bl-br)+(1-b)*(tr-br)
BASE=ground(*ORIGIN)
def local_ground(u,v):return ground(*world(u,v))-BASE
