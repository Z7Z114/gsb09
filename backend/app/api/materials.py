from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/materials", tags=["materials"])


@router.get("/woods", response_model=List[schemas.WoodMaterial])
def list_woods(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200),
               db: Session = Depends(get_db)):
    woods = db.query(models.WoodMaterial).offset(skip).limit(limit).all()
    return woods


@router.get("/woods/{wood_id}", response_model=schemas.WoodMaterial)
def get_wood(wood_id: int, db: Session = Depends(get_db)):
    wood = db.query(models.WoodMaterial).filter(models.WoodMaterial.id == wood_id).first()
    if not wood:
        raise HTTPException(status_code=404, detail="Wood material not found")
    return wood


@router.post("/woods", response_model=schemas.WoodMaterial)
def create_wood(wood: schemas.WoodMaterialCreate, db: Session = Depends(get_db)):
    db_wood = models.WoodMaterial(**wood.dict())
    db.add(db_wood)
    db.commit()
    db.refresh(db_wood)
    return db_wood


@router.get("/bow-parts", response_model=List[schemas.BowPart])
def list_bow_parts(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200),
                   db: Session = Depends(get_db)):
    parts = db.query(models.BowPart).offset(skip).limit(limit).all()
    return parts


@router.get("/bow-parts/{part_id}", response_model=schemas.BowPart)
def get_bow_part(part_id: int, db: Session = Depends(get_db)):
    part = db.query(models.BowPart).filter(models.BowPart.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Bow part not found")
    return part


@router.post("/bow-parts", response_model=schemas.BowPart)
def create_bow_part(part: schemas.BowPartCreate, db: Session = Depends(get_db)):
    db_part = models.BowPart(**part.dict())
    db.add(db_part)
    db.commit()
    db.refresh(db_part)
    return db_part


@router.post("/seed-data")
def seed_initial_data(db: Session = Depends(get_db)):
    # 逐条按名称幂等写入：已存在的跳过，只补缺失的，重复调用不产生重复记录
    woods_data = [
            {
                "name": "桦木",
                "scientific_name": "Betula platyphylla",
                "origin": "中国东北、华北",
                "description": "木质细腻坚韧，纹理顺直，是制作弓胎的优质材料。桦木的弹性适中，不易变形，经过特殊处理后可保持长久的弹力。",
                "texture_image": "/images/woods/birch.jpg",
                "suitable_parts": ["弓胎", "弓梢"],
                "properties": {
                    "density": 0.57,
                    "hardness": "中等",
                    "elasticity": "良好",
                    "durability": "高"
                },
                "traditional_usage": "传统角弓制作中，桦木常被用作弓胎的核心材料，其纹理需与弓的受力方向一致，以确保弓的强度和弹性。"
            },
            {
                "name": "橡木",
                "scientific_name": "Quercus",
                "origin": "中国各地均有分布",
                "description": "木质坚硬厚重，纹理粗犷，具有极高的抗弯曲强度。橡木制作的弓不易变形，适合制作重弓。",
                "texture_image": "/images/woods/oak.jpg",
                "suitable_parts": ["弓胎", "弓把"],
                "properties": {
                    "density": 0.75,
                    "hardness": "高",
                    "elasticity": "中等",
                    "durability": "极高"
                },
                "traditional_usage": "满族清弓多采用橡木制作弓胎，配合牛角和牛筋，制成的重弓射程远、威力大。"
            },
            {
                "name": "榆木",
                "scientific_name": "Ulmus pumila",
                "origin": "中国北方地区",
                "description": "榆木纹理通达清晰，硬度与强度适中，具有良好的韧性。经过多年自然干燥后性能稳定。",
                "texture_image": "/images/woods/elm.jpg",
                "suitable_parts": ["弓胎", "弓梢"],
                "properties": {
                    "density": 0.68,
                    "hardness": "中等偏上",
                    "elasticity": "良好",
                    "durability": "高"
                },
                "traditional_usage": "汉族传统弓常用榆木制作弓胎，讲究'干榆湿柳'，榆木需自然阴干三年以上方可使用。"
            },
            {
                "name": "桑木",
                "scientific_name": "Morus alba",
                "origin": "中国长江流域",
                "description": "桑木材质柔韧，纹理细腻，弹性极佳。桑树生长缓慢，木质细密，是制作弓胎的上品材料。",
                "texture_image": "/images/woods/mulberry.jpg",
                "suitable_parts": ["弓胎", "弓梢", "弓把"],
                "properties": {
                    "density": 0.63,
                    "hardness": "中等",
                    "elasticity": "极佳",
                    "durability": "高"
                },
                "traditional_usage": "古法云'桑柘为上'，桑木制作的弓弹性好、射程远，是古代良弓的首选材料。"
            },
            {
                "name": "柘木",
                "scientific_name": "Cudrania tricuspidata",
                "origin": "中国中南、华东地区",
                "description": "柘木材质坚硬致密，色泽金黄，具有'木中黄金'之称。其弹性和韧性俱佳，是制弓的顶级材料。",
                "texture_image": "/images/woods/zhe.jpg",
                "suitable_parts": ["弓胎", "弓梢"],
                "properties": {
                    "density": 0.82,
                    "hardness": "极高",
                    "elasticity": "极佳",
                    "durability": "极高"
                },
                "traditional_usage": "柘木为制弓之上品，古代帝王专用的'天子之弓'多以柘木为胎，配合牛角、牛筋，价值连城。"
            }
        ]

    woods_added = 0
    for wood in woods_data:
        exists = db.query(models.WoodMaterial).filter(
            models.WoodMaterial.name == wood["name"]
        ).first()
        if not exists:
            db.add(models.WoodMaterial(**wood))
            woods_added += 1

    bow_parts_data = [
            {
                "name": "弓胎",
                "traditional_name": "胎",
                "description": "弓的主体骨架，通常由木材制成，决定了弓的基本形状和性能。弓胎需要选用弹性好、不易变形的优质木材。",
                "diagram_coords": {"x": 400, "y": 200, "width": 600, "height": 40},
                "materials": ["柘木", "桑木", "榆木", "桦木", "橡木"],
                "crafting_steps": [
                    {"step": 1, "description": "选材：选用阴干3年以上的优质木材，要求无结疤、纹理顺直"},
                    {"step": 2, "description": "下料：根据弓的设计尺寸锯割出弓胎雏形"},
                    {"step": 3, "description": "刨制：用刨子将弓胎刨削成所需的渐变厚度"},
                    {"step": 4, "description": "校直：用火烤校直弓胎，确保受力均匀"},
                    {"step": 5, "description": "打磨：用砂纸精细打磨表面，为后续贴角贴筋做准备"}
                ]
            },
            {
                "name": "弓角",
                "traditional_name": "角",
                "description": "贴在弓胎内侧的牛角片，用于增强弓的回弹速度和储能能力。水牛角是最常用的材料。",
                "diagram_coords": {"x": 300, "y": 210, "width": 400, "height": 8},
                "materials": ["水牛角", "黄牛角", "牦牛角"],
                "crafting_steps": [
                    {"step": 1, "description": "选角：选用生长6年以上的水牛角，根部厚实部分最佳"},
                    {"step": 2, "description": "蒸煮：将牛角放入水中蒸煮软化"},
                    {"step": 3, "description": "开片：用锯将牛角沿纵向剖开成薄片"},
                    {"step": 4, "description": "打磨：将角片打磨成所需的厚度和弧度"},
                    {"step": 5, "description": "粘贴：用鱼鳔胶将角片粘贴在弓胎内侧"}
                ]
            },
            {
                "name": "弓筋",
                "traditional_name": "筋",
                "description": "贴在弓胎外侧的牛筋层，用于增强弓的拉伸强度。牛筋需要经过特殊处理。",
                "diagram_coords": {"x": 300, "y": 192, "width": 400, "height": 8},
                "materials": ["牛背筋", "鹿筋"],
                "crafting_steps": [
                    {"step": 1, "description": "取筋：选取健壮水牛的背部主筋"},
                    {"step": 2, "description": "晾晒：自然阴干，避免阳光直射"},
                    {"step": 3, "description": "锤打：用木锤反复锤打，使筋纤维松散"},
                    {"step": 4, "description": "拆分：将筋拆分成细纤维"},
                    {"step": 5, "description": "铺层：用鱼鳔胶将筋丝层层粘贴在弓胎外侧"}
                ]
            },
            {
                "name": "弓梢",
                "traditional_name": "梢",
                "description": "弓的两端部分，用于挂弦。弓梢的角度和长度直接影响弓的性能。",
                "diagram_coords": {"x": 100, "y": 180, "width": 80, "height": 80},
                "materials": ["硬木", "牛角", "鹿角"],
                "crafting_steps": [
                    {"step": 1, "description": "选材：选用密度高、硬度大的优质硬木"},
                    {"step": 2, "description": "成形：根据设计要求制作弓梢形状"},
                    {"step": 3, "description": "开槽：在弓梢末端开出弦槽"},
                    {"step": 4, "description": "打磨：精细打磨，确保表面光滑"},
                    {"step": 5, "description": "安装：用胶和销钉将弓梢固定在弓胎两端"}
                ]
            },
            {
                "name": "弓把",
                "traditional_name": "把",
                "description": "弓箭手握持的部分，通常位于弓的中心。弓把需要舒适、防滑，便于控制。",
                "diagram_coords": {"x": 380, "y": 185, "width": 80, "height": 70},
                "materials": ["软木", "皮革", "缠绳"],
                "crafting_steps": [
                    {"step": 1, "description": "制胎：在弓胎中心位置制作弓把基础形状"},
                    {"step": 2, "description": "打磨：将弓把打磨成适合握持的形状"},
                    {"step": 3, "description": "包裹：用软木或皮革包裹弓把"},
                    {"step": 4, "description": "缠绳：用丝线或棉绳紧密缠绕，增加摩擦力"},
                    {"step": 5, "description": "上漆：最后刷上保护漆，防潮防腐"}
                ]
            }
        ]

    bow_parts_added = 0
    for part in bow_parts_data:
        exists = db.query(models.BowPart).filter(
            models.BowPart.name == part["name"]
        ).first()
        if not exists:
            db.add(models.BowPart(**part))
            bow_parts_added += 1

    craftsmen_data = [
            {
                "name": "杨福喜",
                "school": "汉族传统弓",
                "generation": 7,
                "bio": "杨氏弓箭制作技艺第七代传承人，坚守'聚元号'传统工艺，致力于恢复清代皇家弓箭制作技艺。",
                "avatar": "/images/craftsmen/yangfuxi.jpg",
                "contact": "聚元号弓箭铺"
            },
            {
                "name": "阿拉坦",
                "school": "蒙古族角弓",
                "generation": 5,
                "bio": "蒙古族角弓制作传承人，精通传统骑射弓制作技艺，作品融合了游牧民族的实用美学。",
                "avatar": "/images/craftsmen/altan.jpg",
                "contact": "内蒙古民族工艺坊"
            },
            {
                "name": "李占元",
                "school": "满族清弓",
                "generation": 6,
                "bio": "满族清弓制作技艺传承人，擅长制作大拉力重弓，还原了清代八旗军弓的制作工艺。",
                "avatar": "/images/craftsmen/lizhanyuan.jpg",
                "contact": "满族弓箭作坊"
            }
        ]

    craftsmen_added = 0
    for craftsman in craftsmen_data:
        exists = db.query(models.Craftsman).filter(
            models.Craftsman.name == craftsman["name"]
        ).first()
        if not exists:
            db.add(models.Craftsman(**craftsman))
            craftsmen_added += 1
    
    db.commit()
    
    return {
        "message": "Initial data seeded successfully",
        "woods_added": woods_added > 0,
        "bow_parts_added": bow_parts_added > 0,
        "craftsmen_added": craftsmen_added > 0
    }
