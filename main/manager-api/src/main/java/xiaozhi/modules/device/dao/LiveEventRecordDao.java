package xiaozhi.modules.device.dao;

import org.apache.ibatis.annotations.Mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;

import xiaozhi.modules.device.entity.LiveEventRecordEntity;

@Mapper
public interface LiveEventRecordDao extends BaseMapper<LiveEventRecordEntity> {
}