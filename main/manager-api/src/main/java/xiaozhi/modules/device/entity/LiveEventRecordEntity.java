package xiaozhi.modules.device.entity;

import java.math.BigDecimal;
import java.util.Date;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import lombok.Data;

@Data
@TableName("ai_device_live_event_record")
public class LiveEventRecordEntity {
    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("source")
    private String source;

    @TableField("record_id")
    private String recordId;

    @TableField("room_id")
    private String roomId;

    @TableField("room_title")
    private String roomTitle;

    @TableField("event_type")
    private String eventType;

    @TableField("priority")
    private String priority;

    @TableField("actor_id")
    private String actorId;

    @TableField("actor_name")
    private String actorName;

    @TableField("content")
    private String content;

    @TableField("live_heat")
    private BigDecimal liveHeat;

    @TableField("normalized_payload")
    private String normalizedPayload;

    @TableField("raw_payload")
    private String rawPayload;

    @TableField("event_created_at")
    private Date eventCreatedAt;

    @TableField("reported_at")
    private Date reportedAt;

    @TableField("updated_at")
    private Date updatedAt;
}