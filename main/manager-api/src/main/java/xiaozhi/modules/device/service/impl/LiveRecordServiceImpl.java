package xiaozhi.modules.device.service.impl;

import java.math.BigDecimal;
import java.time.ZoneId;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Date;
import java.util.List;
import java.util.Map;

import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import lombok.RequiredArgsConstructor;
import xiaozhi.modules.device.dao.LiveCommandRecordDao;
import xiaozhi.modules.device.dao.LiveEventRecordDao;
import xiaozhi.modules.device.dto.ExternalLiveCommandRecordDTO;
import xiaozhi.modules.device.dto.ExternalLiveEventRecordDTO;
import xiaozhi.modules.device.entity.LiveCommandRecordEntity;
import xiaozhi.modules.device.entity.LiveEventRecordEntity;
import xiaozhi.modules.device.service.LiveRecordService;

@Service
@RequiredArgsConstructor
public class LiveRecordServiceImpl implements LiveRecordService {
    private static final DateTimeFormatter[] DATE_TIME_FORMATTERS = new DateTimeFormatter[] {
            DateTimeFormatter.ISO_LOCAL_DATE_TIME,
            DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")
    };

    private final LiveEventRecordDao liveEventRecordDao;
    private final LiveCommandRecordDao liveCommandRecordDao;
    private final ObjectMapper objectMapper;

    @Override
    public void reportEvent(ExternalLiveEventRecordDTO request) {
        QueryWrapper<LiveEventRecordEntity> wrapper = new QueryWrapper<>();
        wrapper.eq("source", normalizeSource(request.getSource()));
        wrapper.eq("record_id", request.getRecordId());
        LiveEventRecordEntity entity = liveEventRecordDao.selectOne(wrapper);
        if (entity == null) {
            entity = new LiveEventRecordEntity();
            entity.setSource(normalizeSource(request.getSource()));
            entity.setRecordId(request.getRecordId());
            entity.setReportedAt(new Date());
        }
        entity.setRoomId(StringUtils.defaultString(request.getRoomId()));
        entity.setRoomTitle(StringUtils.defaultString(request.getRoomTitle()));
        entity.setEventType(StringUtils.defaultString(request.getEventType()));
        entity.setPriority(StringUtils.defaultString(request.getPriority()));
        entity.setActorId(StringUtils.defaultString(request.getActorId()));
        entity.setActorName(StringUtils.defaultString(request.getActorName()));
        entity.setContent(StringUtils.defaultString(request.getContent()));
        entity.setLiveHeat(request.getLiveHeat() == null ? BigDecimal.ZERO : request.getLiveHeat());
        entity.setNormalizedPayload(writeJson(request.getNormalizedPayload()));
        entity.setRawPayload(writeJson(request.getRawPayload()));
        entity.setEventCreatedAt(parseDate(request.getEventCreatedAt()));
        if (entity.getId() == null) {
            liveEventRecordDao.insert(entity);
        } else {
            liveEventRecordDao.updateById(entity);
        }
    }

    @Override
    public void reportCommand(ExternalLiveCommandRecordDTO request) {
        QueryWrapper<LiveCommandRecordEntity> wrapper = new QueryWrapper<>();
        wrapper.eq("source", normalizeSource(request.getSource()));
        wrapper.eq("record_id", request.getRecordId());
        LiveCommandRecordEntity entity = liveCommandRecordDao.selectOne(wrapper);
        if (entity == null) {
            entity = new LiveCommandRecordEntity();
            entity.setSource(normalizeSource(request.getSource()));
            entity.setRecordId(request.getRecordId());
            entity.setReportedAt(new Date());
        }
        entity.setRoomId(StringUtils.defaultString(request.getRoomId()));
        entity.setRoomTitle(StringUtils.defaultString(request.getRoomTitle()));
        entity.setCommandType(StringUtils.defaultString(request.getCommandType()));
        entity.setPriorityTrack(StringUtils.defaultString(request.getPriorityTrack()));
        entity.setStatus(StringUtils.defaultString(request.getStatus()));
        entity.setTargetDevice(StringUtils.defaultString(request.getTargetDevice()));
        entity.setErrorMessage(StringUtils.defaultString(request.getErrorMessage()));
        entity.setPayload(writeJson(request.getPayload()));
        entity.setCommandCreatedAt(parseDate(request.getCommandCreatedAt()));
        entity.setDispatchedAt(parseDate(request.getDispatchedAt()));
        if (entity.getId() == null) {
            liveCommandRecordDao.insert(entity);
        } else {
            liveCommandRecordDao.updateById(entity);
        }
    }

    @Override
    public List<LiveEventRecordEntity> listEventRecords(int limit) {
        QueryWrapper<LiveEventRecordEntity> wrapper = new QueryWrapper<>();
        wrapper.orderByDesc("id");
        wrapper.last("limit " + sanitizeLimit(limit));
        return liveEventRecordDao.selectList(wrapper);
    }

    @Override
    public List<LiveCommandRecordEntity> listCommandRecords(int limit) {
        QueryWrapper<LiveCommandRecordEntity> wrapper = new QueryWrapper<>();
        wrapper.orderByDesc("id");
        wrapper.last("limit " + sanitizeLimit(limit));
        return liveCommandRecordDao.selectList(wrapper);
    }

    private String normalizeSource(String source) {
        return StringUtils.defaultIfBlank(source, "douyin-live-brain");
    }

    private int sanitizeLimit(int limit) {
        return Math.max(1, Math.min(limit, 200));
    }

    private Date parseDate(String value) {
        if (StringUtils.isBlank(value)) {
            return null;
        }
        for (DateTimeFormatter formatter : DATE_TIME_FORMATTERS) {
            try {
                LocalDateTime dateTime = LocalDateTime.parse(value.trim(), formatter);
                return Date.from(dateTime.atZone(ZoneId.systemDefault()).toInstant());
            } catch (Exception ignored) {
            }
        }
        return null;
    }

    private String writeJson(Map<String, Object> payload) {
        if (payload == null || payload.isEmpty()) {
            return "{}";
        }
        try {
            return objectMapper.writeValueAsString(payload);
        } catch (JsonProcessingException e) {
            return "{}";
        }
    }
}